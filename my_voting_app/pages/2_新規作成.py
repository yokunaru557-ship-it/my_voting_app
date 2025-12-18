import streamlit as st
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
st.set_page_config(page_title="新規議題の作成", page_icon="✨")

set_background("background.png")  # 背景画像の設定
# ▼▼▼ 門番コード（ログインチェック） ▼▼▼
if "logged_in_user" not in st.session_state or st.session_state.logged_in_user is None:
    st.warning("⚠️ このページを見るにはログインが必要です。")
    st.page_link("Home.py", label="ログイン画面へ戻る", icon="🏠")
    st.stop()
st.divider()
# ---------------------------------------------------------
# 状態管理
# ---------------------------------------------------------
if "creation_completed" not in st.session_state:
    st.session_state.creation_completed = False
if "num_options" not in st.session_state:
    st.session_state.num_options = 2

# ---------------------------------------------------------
# 関数：フォームリセット
# ---------------------------------------------------------
def reset_form():
    st.session_state.creation_completed = False
    st.session_state.num_options = 2
    keys_to_clear = ["input_title", "input_author"] + [k for k in st.session_state.keys() if k.startswith("option_")]
    for k in keys_to_clear:
        if k in st.session_state: del st.session_state[k]

# ---------------------------------------------------------
# 関数：選択肢の増減
# ---------------------------------------------------------
def add_option():
    st.session_state.num_options += 1
def remove_option():
    if st.session_state.num_options > 2: st.session_state.num_options -= 1

# =========================================================
# メイン処理
# =========================================================

# 【パターンA】作成完了画面
if st.session_state.creation_completed:
    st.title("✅ 作成完了！")
    st.success("新しい議題を作成しました。")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏠 ホームに戻る", use_container_width=True):
            reset_form()
            st.switch_page("Home.py") 
    with col2:
        if st.button("✨ 続けて新しい議題を作る", type="primary", use_container_width=True):
            reset_form()
            st.rerun()

# 【パターンB】入力画面
else:
    st.title("✨ 新しい議題を作成する")
    st.markdown("チームのみんなに聞いてみたいことを投稿しましょう！")
    
    with st.container(border=True):
        st.subheader("📝 議題の内容")
        title = st.text_input("議題のタイトル", placeholder="例：来週のランチどこ行く？", key="input_title")
        author = st.text_input("作成者名", placeholder="例：山田 太郎", key="input_author")

        # ▼▼▼ 修正箇所：デフォルト値を現在時刻（日本時間）にする ▼▼▼
        # 日本時間の定義
        t_delta = datetime.timedelta(hours=9)
        JST = datetime.timezone(t_delta, 'JST')
        
        # 現在時刻を取得し、使いやすいように「1時間後」を初期値にする
        # （ピッタリ現在時刻だと、作成ボタンを押すまでの数秒で「過去」になってしまいエラーになるため）
        now_jst = datetime.datetime.now(JST) + datetime.timedelta(hours=1)

        # --- 締め切り設定 ---
        st.markdown("##### 📅 締め切り設定")
        col_date, col_hour, col_min = st.columns([2, 1, 1])
        
        with col_date:
            # 今日の日付（日本時間）をセット
            input_date = st.date_input("締め切り日", value=now_jst.date(), min_value=datetime.date.today())
        with col_hour:
            # 現在の「時」をセット
            input_hour = st.number_input("時", min_value=0, max_value=23, value=now_jst.hour, step=1)
        with col_min:
            # 現在の「分」をセット
            input_minute = st.number_input("分", min_value=0, max_value=59, value=now_jst.minute, step=1)
        
        # 日付と時間を合体
        deadline_dt = datetime.datetime.combine(input_date, datetime.time(input_hour, input_minute))
        
        st.markdown("---")

        # --- 回答形式の選択 ---
        st.subheader("🗳️ 回答の形式")
        vote_type = st.radio("形式を選んでください", ["選択肢から選ぶ", "自由記述（テキスト入力）"], horizontal=True)
        
        options_inputs = []
        
        if vote_type == "選択肢から選ぶ":
            st.caption("参加者は用意された選択肢の中から1つを選びます。")
            for i in range(st.session_state.num_options):
                val = st.text_input(f"選択肢 {i+1}", key=f"option_{i}", placeholder=f"選択肢 {i+1} を入力")
                options_inputs.append(val)

            btn_col1, btn_col2, _ = st.columns([1, 1, 3])
            with btn_col1:
                st.button("＋ 選択肢を追加", on_click=add_option)
            with btn_col2:
                st.button("－ 1行削除", on_click=remove_option, disabled=(st.session_state.num_options <= 2))
        else:
            st.info("💡 参加者は自由に文章を入力して回答できるようになります。")

        st.markdown("---")

        # --- 作成ボタン ---
        if st.button("この内容で議題を作成する", type="primary", use_container_width=True):
            
            final_options_str = ""
            is_valid = True

            # 1. タイトルチェック
            if not title:
                st.error("⚠️ タイトルを入力してください！")
                is_valid = False
            
            # 2. 日付チェック（日本時間で判定）
            # 判定用の現在時刻（バッファなしの本当の現在時刻）を再取得
            check_now_jst = datetime.datetime.now(JST)
            
            # 入力された時間を日本時間扱いにする
            deadline_aware = deadline_dt.replace(tzinfo=JST)
            
            if deadline_aware <= check_now_jst:
                st.error("⚠️ 締め切り時間が過去になっています。現在より未来の日時を設定してください。")
                is_valid = False

            # 3. 選択肢チェック
            if vote_type == "選択肢から選ぶ":
                valid_opts = [opt.strip() for opt in options_inputs if opt.strip()]
                if len(valid_opts) < 2:
                    st.error("⚠️ 選択肢は少なくとも2つ以上入力してください。")
                    is_valid = False
                else:
                    final_options_str = "/".join(valid_opts)
            else:
                final_options_str = "FREE_INPUT"

            # 保存処理
            if is_valid:
                try:
                    formatted_deadline = deadline_dt.strftime("%Y-%m-%d %H:%M")
                    current_email = st.session_state.logged_in_user
                    
                    db_handler.add_topic_to_sheet(title, author, final_options_str, formatted_deadline, current_email)
                    
                    st.session_state.creation_completed = True
                    st.rerun() 
                except Exception as e:
                    st.error(f"保存に失敗しました...: {e}")





















