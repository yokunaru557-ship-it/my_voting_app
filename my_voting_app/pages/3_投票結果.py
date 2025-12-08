import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime, timezone, timedelta

# db_handler.py を読み込めるようにパスを通す
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))
import db_handler

# ページ設定
st.set_page_config(page_title="投票結果", page_icon="📊")

st.title("📊 投票結果一覧")

# -----------------------------
# 現在時刻（日本時間）
# -----------------------------
JST = timezone(timedelta(hours=9))
now = datetime.now(JST)

# -----------------------------
# データ取得
# -----------------------------
topics_df = db_handler.get_topics_from_sheet()
votes_df = db_handler.get_votes_from_sheet()

# -----------------------------
# 締め切り済み議題だけ抽出
# -----------------------------
if not topics_df.empty:
    topics_df["deadline"] = pd.to_datetime(topics_df["deadline"], errors="coerce")
    finished_topics = topics_df[topics_df["deadline"] < now]
else:
    finished_topics = pd.DataFrame()

# -----------------------------
# 議題選択ドロップダウン
# -----------------------------
if finished_topics.empty:
    topic_titles = ["（締め切り済み議題がありません）"]
else:
    topic_titles = finished_topics["title"].tolist()

selected_topic = st.selectbox("議題を選択してください", topic_titles)

# -----------------------------
# 表示処理
# -----------------------------
if finished_topics.empty or selected_topic == "（締め切り済み議題がありません）":
    st.info("締め切り済みの議題がありません。")

else:
    topic_row = finished_topics[finished_topics["title"] == selected_topic].iloc[0]
    options = topic_row["options"].split("/")

    topic_votes = votes_df[votes_df["topic_title"] == selected_topic] if not votes_df.empty else pd.DataFrame()

    st.subheader(f"📝 議題：{selected_topic}")

    # 結果表作成
    result = []
    counts = topic_votes["option"].value_counts() if not topic_votes.empty else {}

    for opt in options:
        result.append({
            "選択肢": opt,
            "投票数": int(counts.get(opt, 0))
        })

    result_df = pd.DataFrame(result)

    # 表のみ表示
    st.table(result_df)

# -----------------------------
# 手動更新
# -----------------------------
st.divider()
if st.button("🔄 更新"):
    st.rerun()
