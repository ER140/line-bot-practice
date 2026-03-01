import os
import requests
from bs4 import BeautifulSoup
import datetime
import re

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
    
    # 全てのセル（日付が入る場所）を取得
    cells = soup.find_all(['th', 'td'])
    today = datetime.date.today()
    target_dates = [today + datetime.timedelta(days=i) for i in range(14)]
    
    found_event_text = None
    target_date_obj = None

    for cell in cells:
        text = cell.get_text().strip()
        # スペースを全て除去して「3/7」や「3月7日」の状態にして比較しやすくする
        clean_text = text.replace(" ", "").replace("　", "")
        
        for target in target_dates:
            m = target.month
            d = target.day
            # 3/7, 3/07, 3月7日, 3月07日 の全パターンを作成
            patterns = [
                f"{m}/{d}", f"{m}/{d:02}", 
                f"{m}月{d}日", f"{m}月{d:02}日"
            ]
            
            if any(p in clean_text for p in patterns):
                # 会場記号が含まれているか確認
                if any(k in clean_text for k in VENUE_CONFIG.keys()):
                    print(f"💡 予定を発見: {text} (判定用: {clean_text})")
                    found_event_text = text
                    target_date_obj = target
                    break
        if found_event_text: break
    
    if not found_event_text:
        print("❌ 該当する練習予定が見つかりませんでした。")
        return None, None, None

    # 備考欄の解析
    description = soup.find('div', id='comment').get_text()
    header_date = f"{target_date_obj.month}/{target_date_obj.day}"
    target_header = f"●{header_date}の合奏予定"
    
    # 備考欄の見出しも「3/ 7」などのスペースに対応
    gaso_plan = "備考欄に詳細がありませんでした。"
    # 備考欄から「●3/7」や「●3/ 7」を探す
    search_pattern = rf"●\s?{target_date_obj.month}/\s?{target_date_obj.day}\s?の合奏予定"
    match = re.search(rf"{search_pattern}.*?(?=\n●|\n#|$)", description, re.DOTALL)
    
    if match:
        gaso_plan = match.group(0).strip()
    else:
        print(f"⚠️ 備考欄に '{target_header}' 形式の見出しが見つかりませんでした。")

    return found_event_text, gaso_plan, header_date

def send_to_line(message):
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    group_id = os.environ.get("LINE_GROUP_ID")
    if not token or not group_id:
        print("❌ LINE設定(Secrets)が空です。")
        return
    
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    payload = {"to": group_id, "messages": [{"type": "text", "text": message}]}
    response = requests.post(url, headers=headers, json=payload)
    print(f"LINE応答ステータス: {response.status_code}")
    if response.status_code != 200:
        print(f"LINEエラー内容: {response.text}")

# メイン処理
event_text, gaso_plan, date = get_densuke_data(DENSUKE_URL)
if event_text:
    m = re.search(r'([四ひラ])', event_text)
    if m:
        v = VENUE_CONFIG[m.group(1)]
        msg = f"📢 次回練習のお知らせ\n\n日付：{date}\n場所：{v['name']}\n合奏予定：\n{gaso_plan}\n\n{v['note']}"
        send_to_line(msg)
    else:
        print(f"❌ 会場記号が見つかりませんでした。")
