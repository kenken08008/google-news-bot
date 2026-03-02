from playwright.sync_api import sync_playwright
import feedparser
import gspread
from google.oauth2.service_account import Credentials
import os

# =========================
# GitHub Actions用
# Secretから認証JSONを生成
# =========================
if os.path.exists("credentials.json") is False:
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if creds_json:
        with open("credentials.json", "w", encoding="utf-8") as f:
            f.write(creds_json)

SERVICE_FILE = "credentials.json"

# =========================
# Google Sheets 設定
# =========================
SPREADSHEET_ID = "17np0tNMRxZVxIGiogFk_5DLDBaGKZOOlLY-sOwDFjAI"
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
RSS_URL = "https://news.google.com/rss/search?hl=ja&gl=JP&ceid=JP%3Aja&oc=11&q=intitle%3A%E3%83%95%E3%82%A3%E3%83%B3%E3%83%A9%E3%83%B3%E3%83%89%E3%80%80%20when%3A1d"

# =========================
# 元記事URL取得（canonical優先）
# =========================
def get_original_url(page, url):
    try:
        page.goto(url, timeout=60000)
        page.wait_for_load_state("networkidle")

        # Googleニュースドメインから離れるまで待機
        page.wait_for_function(
            "location.hostname !== 'news.google.com'",
            timeout=20000
        )

        # canonical（正式URL）取得
        canonical = page.locator("link[rel='canonical']").get_attribute("href")

        if canonical:
            return canonical

        return page.url

    except:
        return "取得失敗"

# =========================
# メイン処理
# =========================
def main():
    # シート初期化
    sheet.clear()

    # ヘッダー（タイトルと元記事URLのみ）
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

        for i, entry in enumerate(feed.entries[:10], start=1):
            google_url = entry.link
            original = get_original_url(page, google_url)

            sheet.append_row([
                entry.title,
                original
            ])

            print("書き込み:", i)

        browser.close()

    print("完了しました")

# =========================
# 実行
# =========================
if __name__ == "__main__":
    main()

