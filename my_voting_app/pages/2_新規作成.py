import streamlit as st
import datetime
import sys
import os

# db_handler.py を読み込めるようにパスを通す設定
# (pagesフォルダの中から、一つ上の階層にある db_handler.py を見つけるため)
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))

# さっき作った db_handler.py を読み込む
import db_handler 

# ---------------------------------------------------------
# ページ設定
# ---------------------------------------------------------
st.set_page_config(page_title="新規議題の作成", page_icon="✨")

st.title("✨ 新しい議題を作成する")
st.markdown("チームのみんなに聞いてみたいことを投稿しましょう！")

# 選択肢の数を管理
if "num_options" not in st.session_state:
    st.session_state.num_options = 2

def add_option():
    st.session_state.num_options += 1

def remove_option():
    if st.session_state.num_options > 2:
        st.session_state.num_options -= 1

# ---------------------------------------------------------
# メイン画面
# ---------------------------------------------------------
with st.container(border=True):
    st.subheader("📝 議題の内容")
    title = st.text_input("議題のタイトル", placeholder="例：来週のランチどこ行く？")
    
    col_a, col_b = st.columns(2)
    with col_a:
        author = st.text_input("作成者名", placeholder="例：山田 太郎")
    with col_b:
        deadline = st.date_input("締め切り日", min_value=datetime.date.today())
    
    st.markdown("---")
    
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

    # 送信ボタン
    if st.button("この内容で議題を作成する", type="primary", use_container_width=True):
        # 空欄を除去
        valid_options = [opt.strip() for opt in options_inputs if opt.strip()]

        if not title:
            st.error("⚠️ タイトルを入力してください！")
        elif len(valid_options) < 2:
            st.error("⚠️ 選択肢は少なくとも2つ以上入力してください。")
        else:
            options_str = "/".join(valid_options)
            
            # ▼▼▼ ここが重要！ CSVではなくスプレッドシートに保存 ▼▼▼
            try:
                # db_handlerを使ってスプレッドシートに書き込む
                db_handler.add_topic_to_sheet(title, author, options_str, deadline)
                
                st.success(f"✅ 議題「{title}」を作成しました！")
                st.balloons()
            except Exception as e:
                # もし設定ミスなどで保存できなかったらエラーを表示
                st.error(f"スプレッドシートへの保存に失敗しました...: {e}")

            st.balloons()



