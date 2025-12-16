import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import streamlit as st
import os
import datetime

# ---------------------------------------------------------
# 設定
# ---------------------------------------------------------
SPREADSHEET_NAME = "voting_app_db"
KEY_FILE = "key.json"

# ---------------------------------------------------------
# Googleスプレッドシートに接続する関数
# ---------------------------------------------------------
def connect_to_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    
    creds = None
    if os.path.exists(KEY_FILE):
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(KEY_FILE, scope)
        except Exception as e:
            st.error(f"認証ファイル(key.json)の読み込みエラー: {e}")
            return None
    else:
        try:
            if "gcp_service_account" in st.secrets:
                key_dict = dict(st.secrets["gcp_service_account"])
                creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)
            else:
                return None
        except Exception as e:
            st.error(f"Secrets認証情報の読み込みエラー: {e}")
            return None

    try:
        client = gspread.authorize(creds)
        sheet = client.open(SPREADSHEET_NAME)
        return sheet
    except Exception as e:
        st.error(f"接続エラー: {e}")
        return None

# ---------------------------------------------------------
# 1. 議題を保存する
# ---------------------------------------------------------
def add_topic_to_sheet(title, author, options, deadline, owner_email):
    sheet = connect_to_sheet()
    if sheet is None: return
    
    try:
        worksheet = sheet.worksheet("topics")
        t_delta = datetime.timedelta(hours=9)
        JST = datetime.timezone(t_delta, 'JST')
        created_at = datetime.datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
        
        # タイトル, 作成者, 選択肢, 期限, 作成日, ステータス, 作成者メアド
        new_row = [title, author, options, str(deadline), created_at, "active", owner_email]
        
        worksheet.append_row(new_row)
    except Exception as e:
        st.error(f"書き込みエラー: {e}")

# ---------------------------------------------------------
# 2. 議題を読み込む
# ---------------------------------------------------------
def get_topics_from_sheet():
    sheet = connect_to_sheet()
    if sheet is None: return pd.DataFrame()
    
    try:
        worksheet = sheet.worksheet("topics")
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"読み込みエラー: {e}")
        return pd.DataFrame()

# ---------------------------------------------------------
# 3. 投票を保存する（ここを更新！）
# ---------------------------------------------------------
# 引数に user_email を追加しました
def add_vote_to_sheet(topic_title, option, user_email):
    sheet = connect_to_sheet()
    if sheet is None: return
    
    try:
        worksheet = sheet.worksheet("votes")
        t_delta = datetime.timedelta(hours=9)
        JST = datetime.timezone(t_delta, 'JST')
        voted_at = datetime.datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
        
        # ▼▼▼ 最後に user_email を保存します ▼▼▼
        new_row = [topic_title, option, voted_at, user_email]
        
        worksheet.append_row(new_row)
    except Exception as e:
        st.error(f"投票書き込みエラー: {e}")

# ---------------------------------------------------------
# 4. 投票数を集計する
# ---------------------------------------------------------
def get_votes_from_sheet():
    sheet = connect_to_sheet()
    if sheet is None: return pd.DataFrame()
    
    try:
        worksheet = sheet.worksheet("votes")
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"投票読み込みエラー: {e}")
        return pd.DataFrame()



# ---------------------------------------------------------
# 4. 議題データ削除
# -----------------------------------------------------
def delete_topic(topic_title, owner_email, logical=True):
    """
    topic_title: 削除対象の議題タイトル
    owner_email: 削除権限を持つユーザーのメールアドレス
    logical: True = 論理削除, False = 物理削除
    """
    sheet = connect_to_sheet()
    if sheet is None:
        return False

    try:
        worksheet = sheet.worksheet("topics")
        records = worksheet.get_all_records()
        df = pd.DataFrame(records)

        # 自分が作成した議題のみ削除対象
        target_rows = df[(df["title"] == topic_title) & (df["owner_email"] == owner_email)]

        if target_rows.empty:
            return False  # 削除対象なし

        for idx in target_rows.index:
            # gspread は行番号 1始まり + ヘッダー行があるので +2
            row_number = idx + 2

            if logical:
                # 論理削除: status を "deleted" に変更
                worksheet.update_cell(row_number, 6, "deleted")
            else:
                # 物理削除: 行ごと削除
                worksheet.delete_row(row_number)

        return True

    except Exception as e:
        st.error(f"削除エラー: {e}")
        return False

# ---------------------------------------------------------
# 5. ステータスを終了にする
# ---------------------------------------------------------
def close_topic_status(topic_title):
    try:
        sheet = connect_to_sheet()
        if sheet is None: return

        worksheet = sheet.worksheet("topics")
        cell = worksheet.find(topic_title)
        # F列(6列目)を closed に書き換える
        worksheet.update_cell(cell.row, 6, "closed")
        
    except Exception as e:
        st.error(f"ステータス更新エラー: {e}")




