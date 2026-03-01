import os
import requests
from bs4 import BeautifulSoup
import datetime
import re

# 会場設定
VENUE_CONFIG = {
    "四": {"name": "四之宮ふれあいセンター 大会議室", "note": "入館の際は「OSGです」。四之宮では「大磯吹奏楽団」の名称は出さないこと。"},
    "ひ": {"name": "ひらしん平塚文化芸術ホール 大練習室", "note": ""},
    "ラ": {"name": "ラディアン マルチルーム1", "note": ""}
}

DENSUKE_URL = "https://densuke.biz/list?cd=BHZuqY9FKUTWu5h7"

def get_densuke_data(url):
    print(f"--- 伝助の解析開始 ---")
    res = requests.get(url)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, 'html.parser')
    
    cells = soup.find_all(['th', 'td'])
    today = datetime.date.today()
    target_dates = [today + datetime.timedelta(days=i) for i in range(14)]
    
    found_event_text = None
    target_date_obj = None

    for cell in cells:
        text = cell.get_text().strip()
        clean_text = text.replace(" ", "").replace("　", "")
        for target in target_dates:
            m, d = target.month, target.day
            patterns = [f"{m}/{d}", f"{m}/{d:02}", f"{m}月{d}日"]
            if any(p in clean_text for p in patterns):
                if any(k in clean_text for k in VENUE_CONFIG.keys()):
                    print(f"💡 予定を発見: {text}")
                    found_event_text = text
                    target_date_obj = target
                    break
        if found_event_text: break
    
    if not found_event_text:
        print("❌ 該当する練習予定が見つかりませんでした。")
        return None, None, None

    # --- 備考欄（コメント）の取得 ---
    comment_area = soup.find('div', id='comment') or soup.find('div', class_='comment') or soup.find('td', class_='comment')
    description = comment_area.get_text() if comment_area else soup.get_text()

    header_date = f"{target_date_obj.month}/{target_date_obj.day}"
    
    # 柔軟な正規表現で「●3/7の合奏予定」から次の「●」か「#」までを抽出
    search_pattern = rf"●\s?{target_date_obj.month}\s?/\s?{target_date_obj.day}\s?の合奏予定"
    match = re.search(rf"({search_pattern}.*?)(?=\n●|\n#|$)", description, re.DOTALL)
    
    if match:
        gaso_plan = match.group(1).strip()
    else:
        # ご指定のメッセージに変更
        print(f"⚠️ 備考欄に '{header_date}' の合奏予定見出しが見つかりませんでした。")
        gaso_plan = "合奏情報が抽出できませんでした"

    return found_event_text, gaso_plan, header_date

def send_to_line(message):
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    group_id = os.environ.get("LINE_GROUP_ID")
    
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    payload = {"to": group_id, "messages": [{"type": "text", "text": message}]}
    response = requests.post(url, headers=headers, json=payload)
    print(f"LINE応答ステータス: {response.status_code}")

# 実行
event_text, gaso_plan, date = get_densuke_data(DENSUKE_URL)

if event_text:
    m = re.search(r'([四ひラ])', event_text)
    if m:
        v = VENUE_CONFIG[m.group(1)]
        msg = f"📢 次回練習のお知らせ\n\n📅 日付：{date}\n📍 場所：{v['name']}\n\n🎼 {gaso_plan}"
        if v['note']:
            msg += f"\n\n⚠️ 備考：\n{v['note']}"
        
        send_to_line(msg)
