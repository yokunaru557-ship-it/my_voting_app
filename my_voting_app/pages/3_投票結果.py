import streamlit as st
import pandas as pd
import sys
import os
from background import set_background
from google import genai

# =========================================================
# Gemini 設定
# =========================================================
API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

# =========================================================
# db_handler.py を読み込めるようにパスを通す
# =========================================================
sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))
import db_handler

# =========================================================
# ページ設定
# =========================================================
st.set_page_config(page_title="投票結果", page_icon="📊")

st.title("📊 投票結果一覧")
st.caption("締切済みの議題のみ表示します")

set_background("background.png")

# =========================================================
# ログインチェック
# =========================================================
if "logged_in_user" not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("⚠️ このページを見るにはログインが必要です。")
    st.page_link("Home.py", label="ログイン画面へ戻る", icon="🏠")
    st.stop()

# =========================================================
# データ取得
# =========================================================
topics_df = db_handler.get_topics_from_sheet()
votes_df = db_handler.get_votes_from_sheet()

# =========================================================
# 日付処理（締切判定）
# =========================================================
if not topics_df.empty and "deadline" in topics_df.columns:
    topics_df["deadline_parsed"] = pd.to_datetime(
        topics_df["deadline"], errors="coerce"
    )
    topics_df["deadline_date"] = topics_df["deadline_parsed"].dt.date

today = pd.to_datetime("now").date()

# 締切済みのみ
if not topics_df.empty and "deadline_date" in topics_df.columns:
    finished_topics = topics_df[
        topics_df["deadline_date"].notna() &
        (topics_df["deadline_date"] < today)
    ].copy()
else:
    finished_topics = pd.DataFrame()

# =========================================================
# 議題選択
# =========================================================
if finished_topics.empty:
    topic_titles = ["（締切済みの議題がありません）"]
else:
    topic_titles = finished_topics["title"].tolist()

selected_topic = st.selectbox("議題を選択してください", topic_titles)

# =========================================================
# 表示モード切替（追加機能）
# =========================================================
view_mode = st.radio(
    "表示方法を選択してください",
    ["全体の投票結果", "自分が投票した内容だけ"],
    horizontal=True
)

# =========================================================
# 表示処理
# =========================================================
if finished_topics.empty or selected_topic == "（締切済みの議題がありません）":
    st.info("締切済みの議題はまだありません。")

else:
    topic_row = finished_topics[
        finished_topics["title"] == selected_topic
    ].iloc[0]

    options = topic_row["options"].split("/")

    # 議題で投票を絞る
    topic_votes = votes_df[
        votes_df["topic_title"] == selected_topic
    ] if not votes_df.empty else pd.DataFrame()

    # 自分の投票だけ表示
    if view_mode == "自分が投票した内容だけ":
        if "user" in topic_votes.columns:
            topic_votes = topic_votes[
                topic_votes["user"] == st.session_state.logged_in_user
            ]
        else:
            st.warning("投票データに user 列が存在しません。")

    st.subheader(f"📝 議題：{selected_topic}")

    # =====================================================
    # 集計
    # =====================================================
    counts = (
        topic_votes["option"].value_counts()
        if not topic_votes.empty else {}
    )

    result = []
    for opt in options:
        result.append({
            "選択肢": opt,
            "投票数": int(counts.get(opt, 0))
        })

    result_df = pd.DataFrame(result)

    # 表表示（インデックス非表示）
    st.dataframe(result_df, hide_index=True)

    # =====================================================
    # Gemini 分析
    # =====================================================
    st.subheader("🔍 Gemini による投票結果分析")

    if st.button("AIに分析してもらう"):
        with st.spinner("Gemini が分析中です..."):

            analysis_prompt = f"""
# 命令
あなたは厳格で経験豊富なデータアナリストです。
以下の制約とテンプレートを必ず守って分析してください。

## 制約
- CSVの生データは出力しない
- テンプレート外の文章は禁止
- 数値は太字で強調
- 客観的に記述する

## 出力テンプレート
---
## 📊 分析概要
（最も重要な結論を2〜3行）

## 📈 投票傾向
- **傾向1**: 詳細
- **傾向2**: 詳細

## 🧠 支持理由の推測
- **理由1**
- **理由2**

## 🔍 全体の特徴・特異点
- 特徴1
- 特徴2

## 解析対象
議題: {selected_topic}
CSV:
{result_df.to_csv(index=False)}
"""

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=analysis_prompt
            )

            st.write(response.text)

# =========================================================
# 更新ボタン
# =========================================================
st.divider()
if st.button("🔄 更新"):
    st.rerun()



