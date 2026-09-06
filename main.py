import os
import requests
from playwright.sync_api import sync_playwright

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.environ.get("LINE_USER_ID")

# 2026年10月25日の対象路線URL
TARGET_URL = "https://secure.j-bus.co.jp/hon/Route/hokkaidosouth_hokkaidocentral?dtym=202610&dtdd=25&filltertext="
TARGET_BUS_NAME = "0126"

def check_bus_seat():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("ページにアクセス中...")
        page.goto(TARGET_URL, wait_until="networkidle")

        page_text = page.inner_text("body")
        
        is_available = False

        if TARGET_BUS_NAME in page_text:
            lines = page_text.split("\n")
            for i, line in enumerate(lines):
                if TARGET_BUS_NAME in line:
                    surrounding_text = " ".join(lines[max(0, i-2):min(len(lines), i+5)])
                    print(f"検出された対象便の情報: {surrounding_text}")
                    
                    # 満席・受付終了以外の状態（○、△、空席、予約など）を検知
                    if any(mark in surrounding_text for mark in ["○", "△", "空席", "予約", "残り"]):
                        if "満席" not in surrounding_text and "受付終了" not in surrounding_text:
                            is_available = True
                    break

        browser.close()

        if is_available:
            message = f"【空席検知！】\n発車オーライネット {TARGET_BUS_NAME}便に空席が出た可能性があります！\n\n予約サイトはこちら：\n{TARGET_URL}"
            send_line_message(message)
            print("空席を検知し、LINE通知を送信しました。")
        else:
            print("現在は満席、または空席が確認できませんでした。")

def send_line_message(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    data = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": message}]
    }
    res = requests.post(url, headers=headers, json=data)
    if res.status_code != 200:
        print(f"LINE送信エラー: {res.status_code}, {res.text}")

if __name__ == "__main__":
    check_bus_seat()
