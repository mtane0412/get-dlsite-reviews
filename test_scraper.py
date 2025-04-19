import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
from scraper import get_all_reviews, get_review_page

def save_html_to_file(html_content, filename="response.html"):
    """
    HTMLの内容をファイルに保存するのだ
    """
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"HTMLを{filename}に保存したのだ")

def test_direct_request():
    """
    直接リクエストを送信してHTMLを確認するのだ
    """
    print("直接リクエストテストを開始するのだ...")
    
    # テスト用のproduct_id
    product_id = "RJ323439"
    url = f"https://www.dlsite.com/maniax/work/reviewlist/=/page/1/product_id/{product_id}.html"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
        "Referer": "https://www.dlsite.com/",
        "Cookie": "adultchecked=1"  # 年齢確認済みクッキー
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        print(f"ステータスコード: {response.status_code}")
        print(f"コンテンツタイプ: {response.headers.get('Content-Type')}")
        
        # HTMLを保存
        save_html_to_file(response.text)
        
        soup = BeautifulSoup(response.text, "html.parser")
        print(f"タイトル: {soup.title.text if soup.title else 'タイトルなし'}")
        
        # すべてのdiv要素のクラスを確認
        div_classes = set()
        for div in soup.find_all("div", class_=True):
            for class_name in div.get("class", []):
                div_classes.add(class_name)
        print(f"ページ内のdivクラス一覧: {sorted(list(div_classes))[:20]}...")
        
        # すべてのp要素のクラスを確認
        p_classes = set()
        for p in soup.find_all("p", class_=True):
            for class_name in p.get("class", []):
                p_classes.add(class_name)
        print(f"ページ内のpクラス一覧: {sorted(list(p_classes))}")
        
        # レビュー要素を探す
        reviews = soup.select("div.review_contents")
        print(f"review_contents要素数: {len(reviews)}")
        
        # 別のセレクタも試す
        reviews_alt = soup.select("div.review_item")
        print(f"review_item要素数: {len(reviews_alt)}")
        
        # レビュー関連の要素を探す
        review_desc = soup.select("p.review_desc")
        print(f"review_desc要素数: {len(review_desc)}")
        
        # 任意のレビュー関連のクラス名を探す
        review_elements = soup.find_all(lambda tag: tag.name and any("review" in cls.lower() for cls in tag.get("class", [])))
        print(f"'review'を含むクラス名を持つ要素数: {len(review_elements)}")
        if review_elements:
            for i, elem in enumerate(review_elements[:5]):
                print(f"レビュー関連要素 {i+1}: {elem.name}.{' '.join(elem.get('class', []))}")
        
        return True
    except requests.exceptions.RequestException as e:
        print(f"エラーが発生したのだ: {e}")
        return False

def test_scraper():
    """
    スクレイピング機能のテストを行うのだ
    """
    print("\nスクレイピングテストを開始するのだ...")
    
    # テスト用のproduct_id
    product_id = "RJ323439"
    
    # まず1ページ目を直接取得してテスト
    soup, has_next = get_review_page(product_id, page=1)
    
    if not soup:
        print("ページが取得できなかったのだ...")
        return False
    
    # 最初の1ページだけ取得してテスト
    reviews = get_all_reviews(product_id, max_pages=1)
    
    if not reviews:
        print("レビューが取得できなかったのだ...")
        return False
    
    print(f"{len(reviews)}件のレビューを取得したのだ！")
    
    # 取得したデータの確認
    df = pd.DataFrame(reviews)
    print("\nデータの概要:")
    print(df.info())
    
    # 最初のレビューを表示
    if len(reviews) > 0:
        print("\n最初のレビュー:")
        first_review = reviews[0]
        for key, value in first_review.items():
            if key == "review":
                # レビュー本文は長いので一部だけ表示
                print(f"{key}: {value[:100]}...")
            else:
                print(f"{key}: {value}")
    
    return True

if __name__ == "__main__":
    # まず直接リクエストテストを実行
    direct_result = test_direct_request()
    print(f"\n直接リクエストテスト結果: {'成功' if direct_result else '失敗'}なのだ！")
    
    # 次にスクレイピングテストを実行
    scraper_result = test_scraper()
    print(f"\nスクレイピングテスト結果: {'成功' if scraper_result else '失敗'}なのだ！")