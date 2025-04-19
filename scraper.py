import requests
from bs4 import BeautifulSoup
import re
import time
from typing import Dict, List, Optional, Any, Tuple
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    """
    Seleniumのドライバーをセットアップするのだ
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # ヘッドレスモード
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def get_review_page(product_id: str, page: int = 1) -> Tuple[Optional[BeautifulSoup], bool]:
    """
    指定されたproduct_idとページ番号のレビューページを取得するのだ
    Seleniumを使用してJavaScriptが実行された後のHTMLを取得するのだ
    
    Args:
        product_id: DLsiteの作品ID (例: RJ323439)
        page: ページ番号 (デフォルト: 1)
        
    Returns:
        (BeautifulSoupオブジェクト, 次のページが存在するかどうか)
    """
    url = f"https://www.dlsite.com/maniax/work/reviewlist/=/page/{page}/product_id/{product_id}.html"
    
    try:
        print(f"URLにアクセス中: {url}")
        
        # Seleniumドライバーをセットアップ
        driver = setup_driver()
        
        try:
            # ページにアクセス
            driver.get(url)
            
            # 年齢確認クッキーを設定
            driver.add_cookie({"name": "adultchecked", "value": "1", "domain": ".dlsite.com"})
            driver.get(url)  # クッキー設定後に再度アクセス
            
            # レビューが読み込まれるまで待機（最大30秒）
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.review_item, div.review_contents"))
            )
            
            # ページのHTMLを取得
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            
            # 総レビュー数を取得（ページタイトルから）
            try:
                title_text = driver.title
                total_reviews_match = re.search(r'\((\d+)\)', title_text)
                if total_reviews_match:
                    total_reviews = int(total_reviews_match.group(1))
                    print(f"総レビュー数: {total_reviews}件")
                    # 1ページあたり10件として必要なページ数を計算
                    total_pages = (total_reviews + 9) // 10
                    has_next = page < total_pages
                    print(f"総ページ数: {total_pages}ページ, 次のページ存在: {has_next}")
                else:
                    has_next = False
            except Exception:
                has_next = False
            
            # レビューが存在するか確認
            reviews = soup.select("div.review_item")
            
            if not reviews:
                # 別のセレクタも試してみる
                reviews_alt = soup.select("div.review_contents")
                print(f"代替セレクタでのレビュー数: {len(reviews_alt)}")
                
                if reviews_alt:
                    print("代替セレクタでレビューが見つかったのだ！")
                    return soup, has_next
                
                print("レビューが見つからないのだ...")
                return None, False
                
            return soup, has_next
        finally:
            # ドライバーを終了
            driver.quit()
    except Exception as e:
        print(f"エラーが発生したのだ: {e}")
        return None, False

def extract_review_data(review_element) -> Dict[str, Any]:
    """
    レビュー要素からデータを抽出するのだ
    
    Args:
        review_element: レビュー要素のBeautifulSoupオブジェクト
        
    Returns:
        抽出したレビューデータの辞書
    """
    review_data = {}
    
    try:
        # タイトル
        title_element = review_element.select_one(".reveiw_title_item, .review_title")
        review_data["title"] = title_element.text.strip() if title_element else ""
        
        # 評価
        rate_element = review_element.select_one(".rate.type_review, .review_star .rate")
        rate = ""
        if rate_element:
            rate_class = rate_element.get("class", [])
            rate_match = [cls for cls in rate_class if cls.startswith("rate") and cls != "rate"]
            if rate_match:
                rate = rate_match[0].replace("rate", "")
        review_data["rate"] = rate
        
        # 日付
        date_element = review_element.select_one(".reveiw_date_item, .review_date p")
        review_data["date"] = date_element.text.strip() if date_element else ""
        
        # 著者
        author_element = review_element.select_one(".reveiw_author_item, .review_author span")
        if author_element:
            author_name = author_element.select_one("span[itemprop='name'], a")
            if author_name:
                review_data["author"] = author_name.text.strip().replace(" さん", "")
            else:
                review_data["author"] = author_element.text.strip().replace(" さん", "")
        else:
            review_data["author"] = ""
        
        # 購入済みかどうか
        purchased_element = review_element.select_one(".icon_purchased, .reveiw_purchased")
        review_data["purchased"] = purchased_element is not None
        
        # ネタバレ注意
        attention_element = review_element.select_one(".review_attention")
        review_data["attention"] = attention_element is not None and not (attention_element.parent.get("style") == "display: none;" if attention_element.parent else False)
        
        # レビュー本文
        review_desc = review_element.select_one("p.review_desc")
        if review_desc:
            # <br>タグを改行に置換
            for br in review_desc.find_all("br"):
                br.replace_with("\n")
            review_data["review"] = review_desc.text.strip()
        else:
            review_data["review"] = ""
        
        # ジャンル
        genres = []
        genre_items = review_element.select(".review_select_genre_item")
        for genre_item in genre_items:
            genre_link = genre_item.select_one("a.btn_default")
            if genre_link:
                genres.append(genre_link.text.strip())
        
        review_data["select_genre"] = ";".join(genres)
    
    except Exception as e:
        print(f"レビューデータの抽出中にエラーが発生したのだ: {e}")
        # エラーが発生しても部分的なデータを返す
    
    return review_data

def get_all_reviews(product_id: str, max_pages: int = 100) -> List[Dict[str, Any]]:
    """
    指定されたproduct_idの全レビューを取得するのだ
    
    Args:
        product_id: DLsiteの作品ID (例: RJ323439)
        max_pages: 取得する最大ページ数 (デフォルト: 100)
        
    Returns:
        レビューデータのリスト
    """
    all_reviews = []
    
    # Seleniumドライバーを一度だけ初期化
    driver = setup_driver()
    
    try:
        # 最初のページにアクセスして総レビュー数を取得
        url = f"https://www.dlsite.com/maniax/work/reviewlist/=/page/1/product_id/{product_id}.html"
        driver.get(url)
        
        # 年齢確認クッキーを設定
        driver.add_cookie({"name": "adultchecked", "value": "1", "domain": ".dlsite.com"})
        driver.get(url)  # クッキー設定後に再度アクセス
        
        # レビューが読み込まれるまで待機
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.review_item, div.review_contents"))
        )
        
        # 総レビュー数を取得（ページタイトルから）
        try:
            title_text = driver.title
            total_reviews_match = re.search(r'\((\d+)\)', title_text)
            if total_reviews_match:
                total_reviews = int(total_reviews_match.group(1))
                print(f"総レビュー数: {total_reviews}件")
                # 1ページあたり10件として必要なページ数を計算
                required_pages = min(max_pages, (total_reviews + 9) // 10)
            else:
                required_pages = max_pages
        except Exception:
            required_pages = max_pages
        
        print(f"取得予定ページ数: {required_pages}ページ")
        
        # 各ページを処理
        for page in range(1, required_pages + 1):
            print(f"ページ {page} を取得中なのだ...")
            
            # 直接URLを指定してページにアクセス
            page_url = f"https://www.dlsite.com/maniax/work/reviewlist/=/page/{page}/product_id/{product_id}.html"
            driver.get(page_url)
            
            # レビューが読み込まれるまで待機
            try:
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.review_item, div.review_contents"))
                )
            except Exception as e:
                print(f"ページ {page} の読み込み中にエラーが発生したのだ: {e}")
                break
            
            # ページのHTMLを取得
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            
            # まずdiv.review_itemを探す
            review_elements = soup.select("div.review_item")
            
            # 見つからなければdiv.review_contentsを探す
            if not review_elements:
                review_elements = soup.select("div.review_contents")
                print(f"代替セレクタでレビュー要素を取得したのだ: {len(review_elements)}件")
            
            if not review_elements:
                print(f"ページ {page} にレビューが見つからなかったのだ...")
                break
                
            print(f"ページ {page} から {len(review_elements)}件のレビューを取得したのだ")
            
            for review_element in review_elements:
                review_data = extract_review_data(review_element)
                all_reviews.append(review_data)
            
            # サーバーに負荷をかけないよう少し待機
            time.sleep(2)
    
    finally:
        # ドライバーを終了
        driver.quit()
    
    return all_reviews