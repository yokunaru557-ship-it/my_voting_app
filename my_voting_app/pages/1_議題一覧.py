#%%writefile app.py
import streamlit as st
import pandas as pd
import datetime
import time
import sys
import os
from background import set_background  #  # 背景画像の設定ファイルをインポート
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

set_background("background.png")  # 背景画像の設定
# ---------------------------------------------------------
# 4. ヘッダー
# ---------------------------------------------------------
st.title(APP_HEADER)
st.caption(APP_DESCRIPTION)
st.divider()

# ソート用セッションステート初期化
if "fg" not in st.session_state:
    st.session_state["fg"] = 0  # 0: 締切順, 1: 新着順

# 右寄せでボタンを横並びに配置
col1, col2, col3, col4 = st.columns([0.36, 0.36, 0.14, 0.14])
with col1:
    input_date = st.date_input("締め切り",min_value=datetime.date.today())
   
with col3:
    st.write("")
    st.write("")
    if st.button("⬆️ 昇順"):
        st.session_state.fg = 1
   
with col4:
    st.write("")
    st.write("")
    if st.button("⬇️ 降順"):
        st.session_state.fg = 0
    

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

# 現在日時
now = datetime.datetime.now()

# ---------------------------------------------------------
# 7. 日付と時刻を含む datetime に変換
# ---------------------------------------------------------
topics_df["deadline"] = pd.to_datetime(topics_df["deadline"], errors="coerce", format="%Y-%m-%d %H:%M")

# 締切があるものだけ残す（締切済み非表示）
topics_df = topics_df[topics_df["deadline"].isna() | (topics_df["deadline"] >= now)]

# ソート処理
if st.session_state.fg == 0:  # 締切順（昇順）
    topics_df = topics_df.sort_values("deadline", ascending=True)
elif st.session_state.fg == 1:  # 新着順（降順）
    topics_df = topics_df.sort_values("deadline", ascending=False)
    
# 締切日での検索（input_date でフィルタ）
if input_date:
    filtered_df = topics_df[
        topics_df["deadline"].dt.date == input_date
    ]

    # 該当データがあるか判定
    if filtered_df.empty:
        st.warning("⚠️ 指定した締切日の議題は見つかりませんでした。")
        st.stop()   # これ以降の表示処理を止める
    else:
        topics_df = filtered_df
# ---------------------------------------------------------
# 8. 議題ループ表示
# ---------------------------------------------------------
# ---------------------------------------------------------
# 8. 議題ループ表示
# ---------------------------------------------------------
for index, topic in topics_df.iterrows():

    button_key = f"vote_btn_{index}"     # ✅ ボタン専用キー
    state_key  = f"vote_state_{index}"   # ✅ 状態保存専用キー

    if state_key not in st.session_state:
        st.session_state[state_key] = False
    st.session_state[state_key] = False

    title = topic["title"]
    author = topic.get("author", "不明")
    options = topic["options"].split("/")
    deadline = topic.get("deadline", pd.NaT)

    if pd.notna(deadline):
        deadline_str = deadline.strftime("%Y-%m-%d %H:%M")
    else:
        deadline_str = "未設定"

    with st.container(border=True):
        st.subheader(title)
        st.caption(f"作成者：{author}｜締め切り：{deadline_str}")

        col1, col2 = st.columns([1, 2])

        # 投票UI
        with col1:
            selected_option = st.radio(
                "投票してください",
                options,
                key=f"radio_{index}"
            )

            if st.button(
                "👍 投票する",
                key=button_key,                     # ✅ ボタン専用
                disabled=st.session_state[state_key]  # ✅ 状態専用
            ):
                st.session_state[state_key] = True   # ✅ 安全に代入できる
                db_handler.add_vote_to_sheet(title, selected_option)
                st.success("投票しました！")
                st.balloons()
                time.sleep(3)
                st.rerun()

        # 投票数表示
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




































