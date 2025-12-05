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

# ---------------------------------------------------------
# ✅ 5. スプレッドシートから議題を取得
# ---------------------------------------------------------
topics_df = db_handler.get_topics_from_sheet()

if topics_df.empty:
    st.info("まだ議題が登録されていません。")
    st.stop()

# ---------------------------------------------------------
# ✅ 6. 投票データも取得
# ---------------------------------------------------------
votes_df = db_handler.get_votes_from_sheet()

# ---------------------------------------------------------
# ✅ 7. 議題表示（本番データ）
# ---------------------------------------------------------
for index, topic in topics_df.iterrows():

    title = topic["title"]
    author = topic.get("author", "不明")
    options = topic["options"].split("/")
    deadline = topic.get("deadline", "")
    created_at = topic.get("created_at", "")

    # ✅ この議題の投票データだけ抽出
    topic_votes = votes_df[votes_df["topic_title"] == title] if not votes_df.empty else pd.DataFrame()

    with st.container(border=True):
        st.subheader(title)
        st.caption(f"作成者：{author}｜締切：{deadline}")

        # ✅ 締切チェック
        is_expired = False
        try:
            if datetime.date.today() > datetime.datetime.strptime(deadline, "%Y-%m-%d").date():
                is_expired = True
                st.warning("⏰ この議題は締切済みです")
        except:
            pass

        col1, col2 = st.columns([1, 2])

        # -------------------------
        # ✅ 投票UI
        # -------------------------
        with col1:
            selected_option = st.radio(
                "投票してください",
                options,
                key=f"radio_{index}",
                disabled=is_expired
            )

            if st.button("👍 投票する", key=f"vote_{index}", disabled=is_expired):
                db_handler.add_vote_to_sheet(title, selected_option)
                st.success("投票しました！")
                st.rerun()

        # -------------------------
        # ✅ 集計表示
        # -------------------------
        with col2:
            st.write("### 📊 現在の投票数")

            if topic_votes.empty:
                for opt in options:
                    st.write(f"{opt}：0 票")
            else:
                counts = topic_votes["option"].value_counts()
                for opt in options:
                    st.write(f"{opt}：{counts.get(opt, 0)} 票")
