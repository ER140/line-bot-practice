import os
import requests
from bs4 import BeautifulSoup

def get_densuke_schedule():
    # 伝助のURL（あなたの伝助のURLに書き換えてください）
    url = 'https://densuke.biz/list?cd=BHZuqY9FKUTWu5h7' 
    
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # スケジュール部分の解析（サイトの構造に合わせて調整済み）
    rows = soup.find_all('tr')
    schedule_text = "--- 練習予定お知らせ ---\n"
    found = False

    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 2:
            date = cells[0].get_text(strip=True)
            status = cells[1].get_text(strip=True)
            # 「〇」や特定のキーワードがある場合のみ抽出
            if "○" in status or "17:00" in date: 
                schedule_text += f"📅 {date}\n"
                found = True
    
    if not found:
        return "直近の確定した練習予定は見つかりませんでした。"
    
    return schedule_text

def send_line_message(message):
    token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
    group_id = os.getenv('LINE_GROUP_ID')
    
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    data = {
        'to': group_id,
        'messages': [{'type': 'text', 'text': message}]
    }
    
    res = requests.post(url, headers=headers, json=data)
    print(f"LINE応答ステータス: {res.status_code}")

if __name__ == "__main__":
    # 1. 伝助から情報を取得
    practice_info = get_densuke_schedule()
    # 2. LINEに送信
    send_line_message(practice_info)
