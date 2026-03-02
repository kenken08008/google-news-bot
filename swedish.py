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
# 元記事URL取得（canonical＋og:url＋AMP対応）
# =========================
def get_original_url(page, url):
    try:
        page.goto(url, timeout=180000)  # 3分
        page.wait_for_load_state("networkidle")
        page.wait_for_function(
            "location.hostname !== 'news.google.com'",
            timeout=60000  # 最大1分待機
        )

        # canonicalタグ
        canonical = page.locator("link[rel='canonical']").get_attribute("href")
        if canonical:
            canonical = canonical.split("?")[0]
            if "/amp/" in canonical:
                canonical = canonical.replace("/amp/", "/")
            return canonical

        # canonicalがない場合は og:url を参照
        og_url = page.locator("meta[property='og:url']").get_attribute("content")
        if og_url:
            og_url = og_url.split("?")[0]
            if "/amp/" in og_url:
                og_url = og_url.replace("/amp/", "/")
            return og_url

        # それでもなければ現在のURLを正規化
        current = page.url.split("?")[0]
        if "/amp/" in current:
            current = current.replace("/amp/", "/")
        return current

    except Exception as e:
        print(f"取得失敗: {url} → {e}")
        return "取得失敗"

# =========================
# メイン処理
# =========================
def main():
    sheet.clear()
    sheet.append_row([
        "タイトル",
        "元記事URL"
    ])

    feed = feedparser.parse(RSS_URL)

    with sync_playwright() as p:
        # headless=False + slow_moで人間っぽく
        browser = p.chromium.launch(headless=False, slow_mo=500)
        page = browser.new_page()

        for i, entry in enumerate(feed.entries[:10], start=1):
            google_url = entry.link
            original = get_original_url(page, google_url)

            sheet.append_row([
                entry.title,
                original
            ])

            print(f"{i}: 書き込み完了 → {original}")
            time.sleep(2)  # ページ間で2秒待機

        browser.close()

    print("完了しました")

# =========================
# 実行
# =========================
if __name__ == "__main__":
    main()
