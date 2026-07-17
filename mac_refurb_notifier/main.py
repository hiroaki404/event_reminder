import json
import os
import smtplib
import urllib.request
from email.mime.text import MIMEText

import functions_framework
from dotenv import load_dotenv
load_dotenv()  # .envファイルから環境変数を読み込む


GMAIL_ADDRESS = os.environ.get('GMAIL_ADDRESS')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD')
NOTIFY_TO = os.environ.get('NOTIFY_TO', GMAIL_ADDRESS)

REFURB_URL = 'https://www.apple.com/jp/shop/refurbished/mac'
USER_AGENT = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'
)
BOOTSTRAP_MARKER = 'window.REFURB_GRID_BOOTSTRAP ='

# 絞り込み条件: MacBook Air、メモリ32GB、ストレージ512GBまたは1TB（チップ・価格は問わない）
TARGET_MODEL = 'macbookair'
TARGET_MEMORY_SIZE = '32gb'
TARGET_CAPACITIES = {'512gb', '1tb'}


def fetch_html():
    req = urllib.request.Request(
        REFURB_URL,
        headers={'User-Agent': USER_AGENT, 'Accept-Language': 'ja-JP,ja;q=0.9'},
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        return res.read().decode('utf-8')


def extract_tiles(html):
    idx = html.find(BOOTSTRAP_MARKER)
    if idx == -1:
        raise ValueError('REFURB_GRID_BOOTSTRAPが見つかりませんでした（ページ構造が変わった可能性があります）')
    start = idx + len(BOOTSTRAP_MARKER)
    while start < len(html) and html[start].isspace():
        start += 1
    data, _ = json.JSONDecoder().raw_decode(html, start)
    return data['tiles']


def is_target(tile):
    dims = tile.get('filters', {}).get('dimensions', {})
    return (
        dims.get('refurbClearModel') == TARGET_MODEL
        and dims.get('tsMemorySize') == TARGET_MEMORY_SIZE
        and dims.get('dimensionCapacity') in TARGET_CAPACITIES
    )


def find_matching_products():
    tiles = extract_tiles(fetch_html())
    matched = []
    for tile in tiles:
        if not is_target(tile):
            continue
        matched.append({
            'title': tile.get('title'),
            'price': tile.get('price', {}).get('currentPrice', {}).get('amount'),
            'url': 'https://www.apple.com' + tile.get('productDetailsUrl', ''),
        })
    return matched


def build_email_body(matched):
    lines = ['整備済製品ページにMacBook Air (32GBメモリ / 512GBまたは1TB) が見つかりました。\n']
    for item in matched:
        lines.append(f"- {item['title']} / {item['price']}\n  {item['url']}")
    return '\n'.join(lines)


def send_email(subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = GMAIL_ADDRESS
    msg['To'] = NOTIFY_TO

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, [NOTIFY_TO], msg.as_string())


def check_and_notify():
    matched = find_matching_products()
    if not matched:
        print('該当商品なし')
        return '該当商品なし'

    subject = f'[整備済Mac] MacBook Air (32GB/512GBまたは1TB) {len(matched)}件見つかりました'
    send_email(subject, build_email_body(matched))
    print(f'{len(matched)}件通知しました')
    return f'{len(matched)}件通知しました'


# Cloud Functions用のエントリーポイント
@functions_framework.http
def main(request):
    result = check_and_notify()
    return result


if __name__ == '__main__':
    check_and_notify()
