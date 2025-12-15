import streamlit as st
import pandas as pd
import datetime
import sys
import os
from background import set_background

# パス設定
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))
import db_handler 

# ---------------------------------------------------------
# ページ設定
# ---------------------------------------------------------
st.set_page_config(page_title="議題一覧", page_icon="🗳️", layout="centered")

set_background("background.png")  # 背景画像の設定

# ▼▼▼ 門番コード ▼▼▼
if "logged_in_user" not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("⚠️ このページを見るにはログインが必要です。")
    st.page_link("Home.py", label="ログイン画面へ戻る", icon="🏠")
    st.stop()

# ---------------------------------------------------------
# ヘッダー & フィルタ UI
# ---------------------------------------------------------
st.title("🗳️ 議題一覧")
st.caption("みんなで意見を集めよう！気になる議題に投票できます。")
st.divider()

# ソート用セッションステート
if "fg" not in st.session_state:
    st.session_state["fg"] = 0 

col1, col2, col3, col4 = st.columns([0.36, 0.36, 0.14, 0.14])
with col1:
    input_date = st.date_input("締め切りで絞り込み", value=None)
with col3:
    st.write("")
    st.write("")
    if st.button("⬆️ 昇順"): st.session_state.fg = 1
with col4:
    st.write("")
    st.write("")
    if st.button("⬇️ 降順"): st.session_state.fg = 0

# ---------------------------------------------------------
# データ取得
# ---------------------------------------------------------
@st.cache_data(ttl=30)
def load_topics():
    return db_handler.get_topics_from_sheet()

topics_df = load_topics()

if topics_df.empty:
    st.info("まだ議題が登録されていません。")
    st.stop()

@st.cache_data(ttl=30)
def load_votes():
    return db_handler.get_votes_from_sheet()

votes_df = load_votes()

# ---------------------------------------------------------
# データ加工
# ---------------------------------------------------------
now = datetime.datetime.now()
topics_df["deadline"] = pd.to_datetime(topics_df["deadline"], errors="coerce", format="%Y-%m-%d %H:%M")
topics_df = topics_df[topics_df["deadline"].isna() | (topics_df["deadline"] >= now)]

if st.session_state.fg == 0:
    topics_df = topics_df.sort_values("deadline", ascending=True)
elif st.session_state.fg == 1:
    topics_df = topics_df.sort_values("deadline", ascending=False)
    
if input_date:
    filtered_df = topics_df[topics_df["deadline"].dt.date == input_date]
    if filtered_df.empty:
        st.warning("⚠️ 指定した締切日の議題は見つかりませんでした。")
        st.stop()
    else:
        topics_df = filtered_df

# ---------------------------------------------------------
# 議題ループ表示
# ---------------------------------------------------------
for index, topic in topics_df.iterrows():
    title = topic["title"]
    author = topic.get("author", "不明")
    options_raw = topic["options"]
    deadline = topic.get("deadline", pd.NaT)
    status = topic.get("status", "active")
    owner_email = topic.get("owner_email", "")

    if pd.notna(deadline):
        deadline_str = deadline.strftime("%Y-%m-%d %H:%M")
    else:
        deadline_str = "未設定"

    is_closed = (status == 'closed')

    with st.container(border=True):
        if is_closed:
            st.subheader(f"🔒 {title} (終了)")
        else:
            st.subheader(title)
            
        st.caption(f"作成者：{author}｜締め切り：{deadline_str}")

        # ▼ 終了ボタン表示 ▼
        current_user = str(st.session_state.logged_in_user).strip()
        owner_email_str = str(owner_email).strip()
        if owner_email_str and current_user == owner_email_str and not is_closed:
             with st.popover("⚠️ 投票を締め切る"):
                st.write("本当に終了しますか？")
                if st.button("はい、終了します", key=f"close_{index}", type="primary"):
                    db_handler.close_topic_status(title)
                    load_topics.clear()
                    st.success("終了しました！")
                    st.rerun()

        st.markdown("---")

        col1, col2 = st.columns([1, 1])

        # 左カラム：投票UI
        with col1:
            if is_closed:
                if status == 'closed':
                    st.warning("⛔ 受付終了")
                else:
                    st.warning("⏰ 期限切れ")
            else:
                submit_value = None
                if options_raw == "FREE_INPUT":
                    st.markdown("**回答を入力してください**")
                    submit_value = st.text_area("あなたの意見", key=f"text_{index}")
                else:
                    st.markdown("**選択肢を選んでください**")
                    try:
                        options_list = str(options_raw).split("/")
                        submit_value = st.radio("選択肢", options_list, key=f"radio_{index}", label_visibility="collapsed")
                    except:
                        st.error("データエラー")

                if st.button("👍 投票する", key=f"vote_{index}", type="primary"):
                    if not submit_value:
                        st.error("回答を入力してください")
                    else:
                        db_handler.add_vote_to_sheet(title, submit_value)
                        load_votes.clear()
                        st.success("投票しました！")
                        st.rerun()

        # 右カラム：投票数集計表示（ここを修正！）
        with col2:
            st.write("### 📊 現在の投票数")
            topic_votes = votes_df[votes_df["topic_title"] == title] if not votes_df.empty else pd.DataFrame()
            
            # ▼▼▼ パターン分けして表示 ▼▼▼
            if options_raw == "FREE_INPUT":
                # --- 自由記述の場合 ---
                if topic_votes.empty:
                    st.write("まだ投票はありません")
                else:
                    counts = topic_votes["option"].value_counts()
                    for opt, count in counts.items():
                        st.write(f"・{opt}：{count} 票")
            else:
                # --- 選択肢の場合（ご希望のコード） ---
                # まず選択肢リストを作ります
                try:
                    options = str(options_raw).split("/")
                except:
                    options = []

                if topic_votes.empty:
                    for opt in options:
                        st.write(f"{opt}：0 票")
                else:
                    counts = topic_votes["option"].value_counts()
                    for opt in options:
                        st.write(f"{opt}：{counts.get(opt, 0)} 票")



































