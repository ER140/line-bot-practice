import os
import requests
from bs4 import BeautifulSoup
import datetime
import re

# 会場別設定（スケジュールを固定値で設定）
VENUE_CONFIG = {
    "四": {
        "name": "四之宮ふれあいセンター 大会議室",
        "schedule": "17:00～ 自由練習\n18:35～ チューニングEX\n18:40〜19:20 合奏(40分)",
        "note": "入館の際は「OSGです」。四之宮では「大磯吹奏楽団」の名称は出さないこと。を徹底して下さい。"
    },
    "ひ": {
        "name": "ひらしん平塚文化芸術ホール 大練習室",
        "schedule": "19:00〜 集合、準備\n19:30〜 チューニングEX",
        "note": ""
    },
    "ラ": {
        "name": "ラディアン マルチルーム1",
        "schedule": "18:00〜 自由練習\n18:40〜 チューニングEX",
        "note": ""
    }
}

DENSUKE_URL = "https://densuke.biz/list?cd=BHZuqY9FKUTWu5h7"

def get_densuke_data(url):
    print(f"--- 伝助の解析開始 ---")
    res = requests.get(url)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # 日程を探す（14日以内）
    dates_text = soup.find_all(['th', 'td'], class_=re.compile(r'list_th_item|list_td_item'))
    today = datetime.date.today()
    target_dates = [today + datetime.timedelta(days=i) for i in range(14)]
    
    found_event = None
    target_date_str = ""
    for item in dates_text:
        text = item.get_text().strip().replace(" ", "").replace("　", "")
        for target in target_dates:
            date_str = f"{target.month}/{target.day}"
            date_patterns = [f"{target.month}/{target.day}", f"{target.month}/{target.day:02}"]
            if any(p in text for p in date_patterns):
                if any(k in text for k in VENUE_CONFIG.keys()):
                    found_event = text
                    target_date_str = date_str
                    break
        if found_event: break
    
    if not found_event:
        print("❌ 該当する練習予定が見つかりませんでした。")
        return None, None, None

    # 備考欄から「合奏予定」を抽出
    comment_div = soup.find('div', id='comment') or soup.find('div', class_='comment')
    description = comment_div.get_text() if comment_div else soup.get_text()
    
    target_header = rf"●\s?{target_date_str}\s?の合奏予定"
    if re.search(target_header, description):
        gaso_match = re.search(rf'{target_header}.*?(?=\n●|\n#|$)', description, re.DOTALL)
        gaso_plan = gaso_match.group(0).strip()
    else:
        gaso_plan = "合奏情報が抽出できませんでした"

    return found_event, gaso_plan, target_date_str

def send_to_line(message):
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    group_id = os.environ.get("LINE_GROUP_ID")
    if not token or not group_id:
        return
    
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    payload = {"to": group_id, "messages": [{"type": "text", "text": message}]}
    requests.post(url, headers=headers, json=payload)

# 実行
event_text, gaso_plan, date = get_densuke_data(DENSUKE_URL)

if event_text:
    m = re.search(r'([四ひラ])', event_text)
    if m:
        v_key = m.group(1)
        v = VENUE_CONFIG[v_key]
        
        # メッセージ組み立て
        msg = f"日付：{date}\n"
        msg += f"場所：{v['name']}\n"
        msg += f"{v['schedule']}\n\n"
        msg += f"合奏予定：\n{gaso_plan}"
        
        if v['note']:
            msg += f"\n\n備考：{v['note']}"
            
        msg += f"\n\n伝助URL：{DENSUKE_URL}"
        
        send_to_line(msg)
