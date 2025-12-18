import streamlit as st
import pandas as pd
import plotly.express as px
import time
import sys
import os
from background import set_background  #  # 背景画像の設定ファイルをインポート
from google import genai # gemini api

# 環境変数から API キーを取得
API_KEY = os.getenv('GEMINI_API_KEY')

# Gemini クライアント初期化
client = genai.Client(api_key=API_KEY)


# db_handler.py を読み込めるようにパスを通す
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))
import db_handler



# ページ設定
set_background("background.png")  # 背景画像の設定
st.set_page_config(page_title="投票結果", page_icon="📊")

st.title("📊 投票結果一覧")
st.caption("締切済みの議題のみ表示します")

st.divider()
# ---------------------------------------------------------
# ▼▼▼ 追加：ログインチェック（門番） ▼▼▼
# ---------------------------------------------------------
if "logged_in_user" not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("⚠️ このページを見るにはログインが必要です。")
    st.page_link("Home.py", label="ログイン画面へ戻る", icon="🏠")
    st.stop() # ← ここで読み込みを強制ストップします
# ---------------------------------------------------------

# データ取得
topics_df = db_handler.get_topics_from_sheet()
votes_df = db_handler.get_votes_from_sheet()


# 日付変換
if not topics_df.empty and "deadline" in topics_df.columns:
    topics_df["deadline_parsed"] = pd.to_datetime(
        topics_df["deadline"], errors="coerce"
    )
    


# 今日の日付
now = pd.Timestamp.now(tz="Asia/Tokyo").tz_localize(None)





# ログインユーザー
current_user = str(st.session_state.logged_in_user).strip()

# 締切済み ＋ 自分が作成した議題のみ抽出
if (
    not topics_df.empty
    and {"deadline_parsed", "status", "owner_email"}.issubset(topics_df.columns)
):
    finished_topics = topics_df[
        (
            (
                topics_df["deadline_parsed"].notna()
                & (topics_df["deadline_parsed"] < now)
            )
            | (topics_df["status"] == "closed")
        )
        & (topics_df["owner_email"].astype(str).str.strip() == current_user)
        & (topics_df["status"] != "deleted")  # ← 論理削除済みを除外
    ].copy()
else:
    finished_topics = pd.DataFrame()


# 議題ドロップダウン
if finished_topics.empty:
    topic_titles = ["（自分が作成した締切済みの議題がありません）"]
else:
    topic_titles = finished_topics["title"].tolist()

selected_topic = st.selectbox("議題を選択してください", topic_titles)


# 表示処理
if finished_topics.empty or selected_topic == "（締切済みの議題がありません）":
    st.info("締切済みの議題はまだありません。")

else:
    topic_row = finished_topics[finished_topics["title"] == selected_topic].iloc[0]
    options = topic_row["options"].split("/")

    topic_votes = (
        votes_df[votes_df["topic_title"] == selected_topic]
        if not votes_df.empty else pd.DataFrame()
    )

    st.subheader(f"📝 議題：{selected_topic}")

    # 集計
    result = []
    counts = (
        topic_votes["option"].value_counts()
        if not topic_votes.empty else {}
    )

    for opt in options:
        result.append({
            "選択肢": opt,
            "投票数": int(counts.get(opt, 0))
        })

    result_df = pd.DataFrame(result)

    # 表表示
    st.dataframe(result_df, hide_index=True)

# finished_topics から選択されたトピックの UUID を取得
if not finished_topics.empty and selected_topic in finished_topics["title"].values:
    topic_uuid = finished_topics[finished_topics["title"] == selected_topic]["uuid"].values[0]
else:
    topic_uuid = None

# 削除ボタン
if st.button("🗑️ 議題を削除") and topic_uuid:
    deleted = db_handler.delete_topic_by_uuid(topic_uuid, current_user)
    if deleted:
        st.success(f"「{selected_topic}」を削除しました。")
        time.sleep(3)
        st.rerun()
    else:
        st.error("削除できませんでした（権限がないか既に削除済み）")


if not result_df.empty:
    
    
    fig = px.bar(
        result_df,
        x="選択肢",
        y="投票数",
        text="投票数",
        title=f"議題: {selected_topic} の投票結果"
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(yaxis=dict(dtick=1))  # Y軸を整数刻みに
    
    st.plotly_chart(fig, use_container_width=True)    
    
# =============================
# Gemini による分析
# =============================
st.divider()
st.subheader("🔍 Geminiによる投票結果分析")
if st.button("🧠AIに分析してもらう"):
    with st.spinner("Gemini が分析中です..."):

        analysis_prompt = f"""
# 命令: あなたは厳格で経験豊富なデータアナリストです。
以下の「制約事項」と「出力テンプレート」を**一言一句厳守**し、提供されたCSVデータを分析してください。

# 制約事項 (重要)
1. **生データの隠蔽**: 入力されたCSVデータ自体は、回答に**絶対に**含めないでください。
2. **フォーマット厳守**: 以下の「出力テンプレート」の構造、見出し、箇条書きのスタイルを崩さないでください。
3. **可読性向上**: 重要な数値（得票数やパーセンテージ）やキーワードは **太字** で強調してください。
4. **客観性**: 主観的な感想は排除し、データに基づいた事実と論理的な推測のみを記述してください。
5. **テンプレート外禁止**: テンプレートに書かれていない文言は**絶対に出力しない**でください。
6. **終了条件**: 出力はテンプレートの最終行までで終了すること。

# 出力テンプレート
---
## 📊 分析概要
（ここに、データ全体から読み取れる最も重要な結論を2〜3行で簡潔に記述。）

## 📈 投票傾向
- **（傾向の要約1）**: （具体的な数値を用いる）
- **（傾向の要約2）**
- **（傾向の要約3）**

## 🧠 支持理由の推測
- **（推測される理由1）**
- **（推測される理由2）**

## 🔍 全体の特徴・特異点
- （分布の特徴）
- （特筆すべき点）

# 解析対象データ
議題:{selected_topic}
CSVデータ:{result_df.to_csv(index=False)}
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=analysis_prompt
        )

        st.write(response.text)




























