import streamlit as st
import pandas as pd
import re
import io
import base64
from scraper import get_all_reviews

st.set_page_config(
    page_title="DLsiteのレビューをCSVにする君",
    page_icon="📝",
    layout="wide",
)

def is_valid_product_id(product_id):
    """
    product_idが有効な形式かチェックするのだ
    """
    return bool(re.match(r'^RJ\d+$', product_id))

def get_csv_download_link(df, filename="reviews.csv"):
    """
    DataFrameをCSVとしてダウンロードするためのリンクを生成するのだ
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">CSVをダウンロードするのだ</a>'
    return href

def main():
    st.title("DLsiteのレビューをCSVにする君")
    st.markdown("DLsiteの作品レビューを収集してCSVファイルにするのだ！")
    
    with st.form("input_form"):
        product_id = st.text_input("DLsite作品ID (例: RJ323439)", value="RJ323439")
        max_pages = st.number_input("取得する最大ページ数", min_value=1, max_value=100, value=10)
        submitted = st.form_submit_button("レビューを取得するのだ！")
    
    if submitted:
        if not is_valid_product_id(product_id):
            st.error("無効な作品IDなのだ！ 'RJ'で始まる数字の形式で入力してほしいのだ。")
            return
        
        with st.spinner(f"作品ID: {product_id} のレビューを取得中なのだ..."):
            reviews = get_all_reviews(product_id, max_pages)
            
            if not reviews:
                st.error("レビューが見つからなかったのだ... 作品IDを確認してほしいのだ。")
                return
            
            # DataFrameに変換
            df = pd.DataFrame(reviews)
            
            # 結果を表示
            st.success(f"{len(reviews)}件のレビューを取得したのだ！")
            
            # データの概要を表示
            st.subheader("データの概要")
            st.dataframe(df)
            
            # CSVダウンロードリンク
            st.markdown(get_csv_download_link(df, f"{product_id}_reviews.csv"), unsafe_allow_html=True)
            
            # 評価の分布を表示
            if 'rate' in df.columns and not df['rate'].empty:
                st.subheader("評価の分布")
                rate_counts = df['rate'].value_counts().sort_index()
                rate_chart = pd.DataFrame({
                    '評価': rate_counts.index,
                    '件数': rate_counts.values
                })
                st.bar_chart(rate_chart.set_index('評価'))

if __name__ == "__main__":
    main()