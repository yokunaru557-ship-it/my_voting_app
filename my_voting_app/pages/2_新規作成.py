import streamlit as st
import datetime
import sys
import os
from background import set_background  #  # 背景画像の設定ファイルをインポート

# パス設定
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))
import db_handler 

# ---------------------------------------------------------
# ページ設定
# ---------------------------------------------------------
st.set_page_config(page_title="新規議題の作成", page_icon="✨")

# ---------------------------------------------------------
# 状態管理（完了画面かどうかのフラグ）
# ---------------------------------------------------------
if "creation_completed" not in st.session_state:
    st.session_state.creation_completed = False

# ---------------------------------------------------------
# 関数：フォームをリセットして再作成する
# ---------------------------------------------------------
def reset_form():
    # 完了フラグを下ろす
    st.session_state.creation_completed = False
    # 選択肢の数をリセット
    st.session_state.num_options = 2
    # 入力内容（session_stateに入っている値）を全部消す
    keys_to_clear = ["input_title", "input_author"] + [k for k in st.session_state.keys() if k.startswith("option_")]
    for k in keys_to_clear:
        if k in st.session_state:
            del st.session_state[k]

# ---------------------------------------------------------
# 関数：選択肢の増減
# ---------------------------------------------------------
if "num_options" not in st.session_state:
    st.session_state.num_options = 2

def add_option():
    st.session_state.num_options += 1

def remove_option():
    if st.session_state.num_options > 2:
        st.session_state.num_options -= 1

# =========================================================
# メイン処理：画面の切り替え
# =========================================================

# 【パターンA】作成完了画面（作成成功後にここが表示される）
if st.session_state.creation_completed:
    
    st.title("✅ 作成完了！")
    st.success("新しい議題を作成しました。")
    st.balloons() # ここで風船を飛ばす
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # ホームに戻るボタン
        if st.button("🏠 ホームに戻る", use_container_width=True):
            reset_form()
            # 完了状態をリセットしてからホームへ
            st.session_state.creation_completed = False
            st.switch_page("Home.py") 
    
    with col2:
        # 続けて作成するボタン
        if st.button("✨ 続けて新しい議題を作る", type="primary", use_container_width=True):
            reset_form() # 入力を空にしてリセット
            st.rerun()   # 画面を再読み込みして入力画面に戻る

# 【パターンB】入力画面（通常はこちらが表示される）
else:
    st.title("✨ 新しい議題を作成する")
    st.markdown("チームのみんなに聞いてみたいことを投稿しましょう！")
    
    with st.container(border=True):
        st.subheader("📝 議題の内容")
        # keyを設定することで、リセット時に値を消せるようにします
        title = st.text_input("議題のタイトル", placeholder="例：来週のランチどこ行く？", key="input_title")
        author = st.text_input("作成者名", placeholder="例：山田 太郎", key="input_author")

        # --- 締め切り設定 ---
        st.markdown("##### 📅 締め切り設定")
        col_date, col_hour, col_min = st.columns([2, 1, 1])
        
        with col_date:
            input_date = st.date_input("締め切り日", min_value=datetime.date.today())
        with col_hour:
            input_hour = st.number_input("時", min_value=0, max_value=23, value=12, step=1)
        with col_min:
            input_minute = st.number_input("分", min_value=0, max_value=59, value=0, step=1)

        deadline_dt = datetime.datetime.combine(input_date, datetime.time(input_hour, input_minute))
        
        st.markdown("---")
        
        # --- 選択肢 ---
        st.subheader("🔢 選択肢")
        options_inputs = []
        for i in range(st.session_state.num_options):
            val = st.text_input(f"選択肢 {i+1}", key=f"option_{i}", placeholder=f"選択肢 {i+1} を入力")
            options_inputs.append(val)

        btn_col1, btn_col2, _ = st.columns([1, 1, 3])
        with btn_col1:
            st.button("＋ 選択肢を追加", on_click=add_option)
        with btn_col2:
            st.button("－ 1行削除", on_click=remove_option, disabled=(st.session_state.num_options <= 2))

        st.markdown("---")

        # --- 作成ボタン ---
        if st.button("この内容で議題を作成する", type="primary", use_container_width=True):
            valid_options = [opt.strip() for opt in options_inputs if opt.strip()]

            if not title:
                st.error("⚠️ タイトルを入力してください！")
            elif len(valid_options) < 2:
                st.error("⚠️ 選択肢は少なくとも2つ以上入力してください。")
            else:
                options_str = "/".join(valid_options)
                
                try:
                    formatted_deadline = deadline_dt.strftime("%Y-%m-%d %H:%M")
                    db_handler.add_topic_to_sheet(title, author, options_str, formatted_deadline)
                    
                    # ★成功したら完了フラグを立てて、画面を再読み込みする
                    st.session_state.creation_completed = True
                    st.rerun() 
                    
                except Exception as e:
                    st.error(f"スプレッドシートへの保存に失敗しました...: {e}")










