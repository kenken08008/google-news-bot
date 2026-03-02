from playwright.sync_api import sync_playwright
import feedparser


# ==============================
# 取得したいGoogleニュースRSS
# ==============================
RSS_URL = "https://news.google.com/rss/search?hl=ja&gl=JP&ceid=JP%3Aja&oc=11&q=intitle%3A%E3%83%95%E3%82%A3%E3%83%B3%E3%83%A9%E3%83%B3%E3%83%89%20when%3A1d"


# ==============================
# 元記事URL取得関数（重要）
# ==============================
def get_original_url(page, url):
    try:
        # Googleニュースページを開く
        page.goto(url, timeout=60000)

        # 通信が落ち着くまで待つ
        page.wait_for_load_state("networkidle")

        # news.google.com 以外になるまで待つ（リダイレクト待機）
        page.wait_for_function(
            "location.hostname !== 'news.google.com'",
            timeout=20000
        )

        # 最終URL（元記事）
        return page.url

    except Exception as e:
        return "取得失敗"


# ==============================
# メイン処理
# ==============================
def main():

    print("RSS取得中...")
    feed = feedparser.parse(RSS_URL)

    print("ブラウザ起動中...")

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False,  # 動作を見たい場合False（おすすめ）
            slow_mo=500      # 人間っぽくゆっくり操作
        )

        page = browser.new_page()

        print("取得開始\n")

        for i, entry in enumerate(feed.entries, start=1):

            google_url = entry.link
            original = get_original_url(page, google_url)

            print("ーーーーーーーーーーーーーー")
            print(f"No: {i}")
            print("タイトル:", entry.title)
            print("GoogleURL:", google_url)
            print("元記事:", original)

        browser.close()

    print("\n完了しました")


# ==============================
# 実行
# ==============================
if __name__ == "__main__":
    main()
