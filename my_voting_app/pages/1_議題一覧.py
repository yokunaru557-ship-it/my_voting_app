%%writefile app.py
import streamlit as st
import pandas as pd

# ---------------------------------------------------------
# 1. 設定 & 定数
# ---------------------------------------------------------
PAGE_TITLE = "投票アプリ"
APP_HEADER = "🗳️ 議題一覧"
APP_DESCRIPTION = "みんなで意見を集めよう！気になる議題に投票できます。"

# ---------------------------------------------------------
# 2. ページ設定
# ---------------------------------------------------------
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon="🗳️",
    layout="centered"
)

# ---------------------------------------------------------
# 3. サイドバー（画面遷移メニュー）
# ---------------------------------------------------------
with st.sidebar:
    st.title("📌 メニュー")

    if st.button("🏠 HOME", use_container_width=True):
        st.switch_page("home.py")

    if st.button("📋 議題一覧", use_container_width=True):
        st.switch_page("app.py")

    if st.button("➕ 議題作成", use_container_width=True):
        st.switch_page("pages/create_topic.py")

    if st.button("📊 投票結果", use_container_width=True):
        st.switch_page("pages/results.py")

# ---------------------------------------------------------
# 4. ヘッダー
# ---------------------------------------------------------
st.title(APP_HEADER)
st.caption(APP_DESCRIPTION)
st.divider()

# ---------------------------------------------------------
# 5. 議題リスト（仮データ）
# ---------------------------------------------------------
topics = [
    {"id": 1, "title": "好きなプログラミング言語は？", "votes": 0},
    {"id": 2, "title": "次回のイベント開催場所は？", "votes": 0},
    {"id": 3, "title": "欲しい部活動設備は？", "votes": 0},
]

# ---------------------------------------------------------
# 6. 議題表示（カード風・純正UI）
# ---------------------------------------------------------
for topic in topics:
    with st.container(border=True):
        st.subheader(topic["title"])

        col1, col2 = st.columns([1, 2])

        with col1:
            if st.button("👍 投票する", key=f"vote_{topic['id']}"):
                topic["votes"] += 1
                st.success("投票しました！")

        with col2:
            st.write(f"現在の投票数：{topic['votes']} 票")
