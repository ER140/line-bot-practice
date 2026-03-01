import os
import requests
from bs4 import BeautifulSoup
import datetime
import re

# 会場別設定
VENUE_CONFIG = {
    "四": {
        "name": "四之宮ふれあいセンター 大会議室",
        "free_label": "自由練習",
        "free_time": "17:00〜",
        "tune_time": "18:35〜",
        "note": "入館の際は「OSGです」。四之宮では「大磯吹奏楽団」の名称は出さないこと。を徹底して下さい。"
    },
    "ひ": {
        "name": "ひらしん平塚文化芸術ホール 大練習室",
        "free_label": "集合、準備",
        "free_time": "19:00〜",
        "tune_time": "19:30〜",
        "note": ""
    },
    "ラ": {
        "name": "ラディアン マルチルーム1",
        "free_label": "自由練習",
        "free_time": "18:00〜",
        "tune_time": "18:40〜",
        "note": ""
    }
}

DENSUKE_URL = "https://densuke.biz/list?cd=BHZuqY9FKUTWu5h7"

def get_densuke_data(url):
    res = requests.get(url)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, 'html.parser')
    
    dates_text = soup.find_all('th', class_='list_th_item')
    today = datetime.date.today()
    # 金〜日の直近予定を探す
    target_dates = [today, today + datetime.timedelta(days=1), today + datetime.timedelta(days=2)]
    
    found_event = None
    target_date_str = ""
    for item in dates_text:
        text = item.get_text().strip()
        for target in target_dates:
            date_str = f"{target.month}/{target.day}"
            if date_str in text:
                found_event = text
                target_date_str = date_str
                break
        if found_event: break
    
    if not found_event: return None, None, None

    description = soup.find('div', id='comment').get_text()
    target_header = f"●{target_date_str}の合奏予定"
    
    if target_header in description:
        gaso_match = re.search(rf'{re.escape(target_header)}.*?(?=\n●|\n#|$)', description, re.DOTALL)
        gaso_plan = gaso_match.group(0).strip()
    else:
        gaso_plan = "抽出できませんでした🙏"

    return found_event, gaso_plan, target_date_str

def send_to_line(message):
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    group_id = os.environ.get("LINE_GROUP_ID")
    
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "to": group_id,
        "messages": [{"type": "text", "text": message}]
    }
    requests.post(url, headers=headers, json=payload)

# 実行
event_text, gaso_plan, date = get_densuke_data(DENSUKE_URL)

if event_text:
    m = re.search(r'([四ひラ])', event_text)
    if m:
        v = VENUE_CONFIG[m.group(1)]
        
        msg = f"📢 次回練習のお知らせ [練習連絡BOT]\n\n"
        msg += f"**日付**：{date}\n"
        msg += f"**場所**：{v['name']}\n"
        msg += f"**{v['free_label']}**：{v['free_time']}\n"
        msg += f"**チューニング**：{v['tune_time']}\n\n"
        msg += f"**合奏予定**：\n{gaso_plan}\n"
        
        if v['note']:
            msg += f"\n**備考**：{v['note']}\n"
            
        msg += f"\n**伝助URL**：\n{DENSUKE_URL}\n"
        msg += "\n※このメッセージはBOTにより自動送信されています。"
        
        send_to_line(msg)
