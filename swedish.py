from playwright.sync_api import sync_playwright
import feedparser
import gspread
from google.oauth2.service_account import Credentials
import os
import time

# =========================
# GitHub Actions用
# Secretから認証JSONを生成
# =========================
if not os.path.exists("credentials.json"):
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if creds_json:
        with open("credentials.json", "w", encoding="utf-8") as f:
            f.write(creds_json)

SERVICE_FILE = "credentials.json"

# =========================
# Google Sheets 設定
# =========================
SPREADSHEET_ID = "13US1u2PxZGwUGs_cQ0HcbxAfjEe6rvZMr1g0GF9UYiY"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_file(
    SERVICE_FILE,
    scopes=SCOPES
)
gc = gspread.authorize(creds)
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1

# =========================
# GoogleニュースRSS
# =========================
RSS_URL = "https://news.google.com/rss/search?hl=ja&gl=JP&ceid=JP%3Aja&oc=11&q=intitle%3A%E3%82%B9%E3%82%A6%E3%82%A7%E3%83%BC%E3%83%87%E3%83%B3%20when%3A1d"

# =========================
# 元記事URL取得（canonical優先＋AMP対応）
# =========================
def get_original_url(page, url):
    try:
        page.goto(url, timeout=120000)  # タイムアウト2分
        page.wait_for_load_state("networkidle")

        # Googleニュースから別ドメインへ移動待ち
        page.wait_for_function(
            "location.hostname !== 'news.google.com'",
            timeout=40000
        )

        # canonicalタグ取得
        canonical = page.locator("link[rel='canonical']").get_attribute("href")
        if canonical:
            if "/amp/" in canonical:
                canonical = canonical.replace("/amp/", "/")
            canonical = canonical.split("?")[0]
            return canonical

        # canonicalがなければ現在のURLを正規化
        current = page.url
        if "/amp/" in current:
            current = current.replace("/amp/", "/")
        current = current.split("?")[0]
        return current

    except Exception as e:
        print(f"取得失敗: {url} → {e}")
        return "取得失敗"

# =========================
# メイン処理
# =========================
def main():
    # シート初期化
    sheet.clear()

    # ヘッダー
    sheet.append_row([
        "タイトル",
        "元記事URL"
    ])

    # RSS取得
    feed = feedparser.parse(RSS_URL)

    # Playwright起動
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # RSSから最大10件取得
        for i, entry in enumerate(feed.entries[:10], start=1):
            google_url = entry.link
            original = get_original_url(page, google_url)

            sheet.append_row([
                entry.title,
                original
            ])

            print("書き込み:", i)
            time.sleep(2)  # 2秒待機して人間っぽく

        browser.close()

    print("完了しました")

# =========================
# 実行
# =========================
if __name__ == "__main__":
    main()
