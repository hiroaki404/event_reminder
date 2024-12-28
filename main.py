from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from datetime import datetime, date
import calendar
import os
import functions_framework
from dotenv import load_dotenv
load_dotenv()  # .envファイルから環境変数を読み込む


# Slack APIトークンを設定
SLACK_TOKEN = os.environ.get('SLACK_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')

def get_month_dates():
    today = date.today()
    _, last_day = calendar.monthrange(today.year, today.month)
    start_date = date(today.year, today.month, 1)
    end_date = date(today.year, today.month, last_day)
    return start_date.strftime('%Y%%2F%m%%2F%d'), end_date.strftime('%Y%%2F%m%%2F%d')

def send_message():
    client = WebClient(token=SLACK_TOKEN)
    start_date, end_date = get_month_dates()
    
    message = (
        f"今月のAndroidのイベントは、\n"
        f"https://connpass.com/search/?q=Android&start_from={start_date}"
        f"&start_to={end_date}&prefectures=chiba&prefectures=tokyo"
        f"&selectItem=chiba&selectItem=tokyo&sort="
        f"\nです。"
    )
    
    try:
        response = client.chat_postMessage(
            channel=CHANNEL_ID,
            text=message
        )
        print("メッセージが送信されました！")
        return "メッセージが送信されました！"
    
    except SlackApiError as e:
        return f"エラーが発生しました: {e.response['error']}"

# Cloud Functions用のエントリーポイント
@functions_framework.http
def main(request):
    result = send_message()
    return result

if __name__ == "__main__":
    send_message()