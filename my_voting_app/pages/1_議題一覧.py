#%%writefile app.py
import streamlit as st
import pandas as pd
import datetime
import sys
import os

# ---------------------------------------------------------
# db_handler.py を読み込めるようにパスを通す
# ---------------------------------------------------------
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
import db_handler

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
# 4. ヘッダー
# ---------------------------------------------------------
st.title(APP_HEADER)
st.caption(APP_DESCRIPTION)
st.divider()
if "fg" not in st.session_state:
    st.session_state["fg"] = 0  # 0: 期限順, 1: 新着順
# 2列に分けてボタンを配置
col1, col2 = st.columns([0.3, 0.3])  # 余白は残る
with col1:
    if st.button("⏰ 期限順"):
        st.session_state.fg = 0
with col2:
    if st.button("🆕 新しい順"):
        st.session_state.fg = 1
# ---------------------------------------------------------
# 5. スプレッドシートから議題を取得
# ---------------------------------------------------------
topics_df = db_handler.get_topics_from_sheet()

if topics_df.empty:
    st.info("まだ議題が登録されていません。")
    st.stop()

# ---------------------------------------------------------
# 6. 投票データも取得
# ---------------------------------------------------------
votes_df = db_handler.get_votes_from_sheet()

# 今日の日付
today = datetime.date.today()

# 今日の日付
today = datetime.date.today()

# 1. created_at や deadline を date 型に変換
topics_df["deadline"] = pd.to_datetime(topics_df["deadline"], errors="coerce").dt.date

# 2. 締切があるものだけ残す（締切済みを非表示）
topics_df = topics_df[topics_df["deadline"].isna() | (topics_df["deadline"] >= today)]

# 3. 締切日で昇順ソート（期限が近いものから表示）
if st.session_state.fg == 0:
    topics_df = topics_df.sort_values("deadline", ascending=True)
# 3. 締切日で降順ソート（期限が遠いものから表示）
if st.session_state.fg == 1:
    topics_df = topics_df.sort_values("deadline", ascending=False)

# 4. ループで表示
for index, topic in topics_df.iterrows():
    title = topic["title"]
    author = topic.get("author", "不明")
    options = topic["options"].split("/")
    deadline = topic.get("deadline", "")

    with st.container(border=True):
        st.subheader(title)
        st.caption(f"作成者：{author}｜締切：{deadline}")

        col1, col2 = st.columns([1, 2])

        with col1:
            selected_option = st.radio(
                "投票してください",
                options,
                key=f"radio_{index}"
            )
            if st.button("👍 投票する", key=f"vote_{index}"):
                db_handler.add_vote_to_sheet(title, selected_option)
                st.success("投票しました！")
                st.rerun()

        with col2:
            st.write("### 📊 現在の投票数")
            topic_votes = votes_df[votes_df["topic_title"] == title] if not votes_df.empty else pd.DataFrame()
            if topic_votes.empty:
                for opt in options:
                    st.write(f"{opt}：0 票")
            else:
                counts = topic_votes["option"].value_counts()
                for opt in options:
                    st.write(f"{opt}：{counts.get(opt, 0)} 票")







