import os
import requests
from bs4 import BeautifulSoup
import datetime
import re

# 会場別設定（スケジュール固定）
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
    
    # 伝助のテーブルから全セルを取得
    cells = soup.find_all(['th', 'td'], class_=re.compile(r'list_th_item|list_td_item'))
    today = datetime.date.today()
    # 今日から14日以内をスキャン（3/7を確実に含むため）
    target_dates = [today + datetime.timedelta(days=i) for i in range(14)]
    
    found_event = None
    target_date_str = ""

    for cell in cells:
        # セル内のテキストを取得し、全角スペースなどを正規化
        text = cell.get_text().strip()
        # 判定用に「スペース」「0」を除去した文字列も用意
        normalized_text = text.replace(" ", "").replace("　", "").replace("/0", "/")
        
        for target in target_dates:
            m, d = target.month, target.day
            
            # --- 全方位対応の正規表現パターン ---
            # 3/7, 3/ 7, 3/07, 3月7日, 3月07日 をすべて網羅
            patterns = [
                rf"{m}/{d}",           # 3/7
                rf"{m}/\s?{d}",        # 3/ 7 (スペースあり)
                rf"{m}/{d:02}",        # 3/07
                rf"{m}月{d}日",        # 3月7日
                rf"{m}月{d:02}日"      # 3月07日
            ]
            
            if any(re.search(p, text) for p in patterns):
                # 会場記号が含まれているかチェック
                if any(k in normalized_text for k in VENUE_CONFIG.keys()):
                    found_event = text
                    target_date_str = f"{m}/{d}"
                    print(f"✅ 予定を発見しました: {text}")
                    break
        if found_event: break
    
    if not found_event:
        print("❌ 該当する日付・会場の予定が見つかりませんでした。")
        return None, None, None

    # 備考欄（コメント）の取得
    comment_div = soup.find('div', id='comment') or soup.find('div', class_='comment') or soup.find('td', class_='comment')
    description = comment_div.get_text() if comment_div else soup.get_text()

    # 合奏予定の抽出（柔軟なマッチング）
    # 「● 3 / 7 の合奏予定」のようなゆらぎにも対応
    header_pattern = rf"●\s?{target_date_str.split('/')[0]}\s?/\s?{target_date_str.split('/')[1]}\s?の合奏予定"
    
    match = re.search(rf"({header_pattern}.*?)(?=\n●|\n#|$)", description, re.DOTALL)
    
    if match:
        gaso_plan = match.group(1).strip()
    else:
        gaso_plan = "合奏情報が抽出できませんでした"

    return found_event, gaso_plan, target_date_str

def send_to_line(message):
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    group_id = os.environ.get("LINE_GROUP_ID")
    if not token or not group_id:
        print("❌ Secrets (TOKEN または GROUP_ID) が設定されていません。")
        return
    
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    payload = {"to": group_id, "messages": [{"type": "text", "text": message}]}
    response = requests.post(url, headers=headers, json=payload)
    print(f"LINE応答ステータス: {response.status_code}")

# 実行
event_text, gaso_plan, date = get_densuke_data(DENSUKE_URL)

if event_text:
    # 会場記号を判別
    m = re.search(r'([四ひラ])', event_text)
    if m:
        v_key = m.group(1)
        v = VENUE_CONFIG[v_key]
        
        # 指定のフォーマットに組み立て
        msg = f"日付：{date}\n"
        msg += f"場所：{v['name']}\n"
        msg += f"{v['schedule']}\n\n"
        msg += f"合奏予定：\n{gaso_plan}"
        
        if v['note']:
            msg += f"\n\n備考：{v['note']}"
            
        msg += f"\n\n伝助URL：{DENSUKE_URL}"
        
        send_to_line(msg)
