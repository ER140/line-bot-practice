import os

def check_id():
    group_id = os.getenv('LINE_GROUP_ID')
    token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
    
    print("--- ID調査モード開始 ---")
    print(f"現在設定されているID: {group_id}")
    print(f"IDの文字数: {len(group_id)}")
    
    if not group_id.startswith('C'):
        print("⚠️ 警告: グループIDは通常 'C' から始まります。")
    
    # ダミーのメッセージを送ってみて、エラーの詳細を見る
    import requests
    import json
    
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    data = {
        'to': group_id,
        'messages': [{'type': 'text', 'text': 'IDテスト送信'}]
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    print(f"LINE応答ステータス: {response.status_code}")
    print(f"LINEエラー詳細: {response.text}")
    print("--- 調査終了 ---")

if __name__ == "__main__":
    check_id()
