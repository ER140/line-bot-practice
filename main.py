import os
import requests
from bs4 import BeautifulSoup
import datetime
import re

VENUE_CONFIG = {
    "四": {"name": "四之宮ふれあいセンター 大会議室", "free_label": "自由練習", "free_time": "17:00〜", "tune_time": "18:35〜", "note": "入館の際は「OSGです」。四之宮では「大磯吹奏楽団」の名称は出さないこと。"},
    "ひ": {"name": "ひらしん平塚文化芸術ホール 大練習室", "free_label": "集合、準備", "free_time": "19:00〜", "tune_time": "19:30〜", "note": ""},
    "ラ": {"name": "ラディアン マルチルーム1", "free_label": "自由練習", "free_time": "18:00〜", "tune_time": "18:40〜", "note": ""}
}

DENSUKE_URL = "https://densuke.biz/list?cd=BHZuqY9FKUTWu5h7"

def get_densuke_data(url):
    print(f"--- 伝助の解析開始 ---")
    res = requests.get(url)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # 伝助の表の見出し（日付部分）をすべて取得
    dates_text = soup.find_all('th', class_='list_th_item')
    today = datetime.date.today()
    
    # 今後14日間を検索対象にする
    target_dates = [today + datetime.timedelta(days=i) for i in range(14)]
    
    found_event = None
    target_date_obj = None

    for item in dates_text:
        text = item.get_text().strip()
        for target in target_dates:
            # 「3」と「7」が両方含まれているかチェック（月/日 形式）
            # これなら「3/7」でも「3月7日」でも「3月07日」でもヒットします
            month_str = str(target.month)
            day_str = str(target.day)
            
            # 月と日がテキスト内に存在するか確認
            if month_str in text and day_str in text:
                print(f"💡 伝助の中に予定を発見: {text}")
                found_event = text
                target_date_obj = target
                break
        if found_event: break
    
    if not found_event:
        print("❌ 該当する日付の予定が伝助の表に見当たりませんでした。")
        # デバッグ用：今伝助にある文字を表示
        print(f"伝助にあった文字の例: {[d.get_text().strip() for d in dates_text[:5]]}")
        return None, None, None

    description = soup.find('div', id='comment').get_text()
    header_date = f"{target_date_obj.month}/{target_date_obj.day}"
    target_header = f"●{header_date}の合奏予定"
    
    if target_header in description:
        gaso_match = re.search(rf'{re.escape(target_header)}.*?(?=\n●|\n#|$)', description, re.DOTALL)
        gaso_plan = gaso_match.group(0).strip()
    else:
        print(f"⚠️ 備考欄に '{target_header}' が見つかりませんでした。")
        gaso_plan = "備考欄に詳細がありませんでした。"

    return found_event, gaso_plan, header_date

def send_to_line(message):
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    group_id = os.environ.get("LINE_GROUP_ID")
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    payload = {"to": group_id, "messages": [{"type": "text", "text": message}]}
    response = requests.post(url, headers=headers, json=payload)
    print(f"LINE応答ステータス: {response.status_code}")
    if response.status_code != 200:
        print(f"LINEエラー内容: {response.text}")

# 実行
event_text, gaso_plan, date = get_densuke_data(DENSUKE_URL)

if event_text:
    m = re.search(r'([四ひラ])', event_text)
    if m:
        v = VENUE_CONFIG[m.group(1)]
        msg = f"📢 次回練習のお知らせ\n\n日付：{date}\n場所：{v['name']}\n合奏予定：\n{gaso_plan}"
        send_to_line(msg)
    else:
        print(f"❌ 予定名 '{event_text}' に会場記号[四, ひ, ラ]がありません。")
