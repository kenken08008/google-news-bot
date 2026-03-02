import time
import csv
from playwright.sync_api import sync_playwright

# ===============================
# 設定
# ===============================

# 入力ファイル（GoogleニュースRSSなどから取得したURL一覧）
INPUT_FILE = "input.csv"

# 出力ファイル（リダイレクト後URL）
OUTPUT_FILE = "output.csv"

# 待機秒（Google対策：少し待つ）
WAIT_SECONDS = 5


# ===============================
# リダイレクトURL取得関数
# ===============================
def get_redirect_url(page, url):
    try:
        print("アクセス:", url)

        page.goto(url, timeout=60000)

        # ページが安定するまで待つ
        page.wait_for_load_state("networkidle")

        # 少し待つ（超重要：bot対策）
        time.sleep(WAIT_SECONDS)

        # 現在URLを取得（リダイレクト後）
        final_url = page.url
        print("取得:", final_url)

        return final_url

    except Exception as e:
        print("取得失敗:", e)
        return "取得失敗"


# ===============================
# メイン処理
# ===============================
def main():

    # CSV読み込み
    with open(INPUT_FILE, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        urls = [row[0] for row in reader if row]

    results = []

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True,  # GitHub Actionsは必ずTrue
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
        )

        page = context.new_page()

        for url in urls:
            redirect = get_redirect_url(page, url)
            results.append([url, redirect])

        browser.close()

    # CSV書き込み
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["元URL", "リダイレクト後URL"])
        writer.writerows(results)

    print("完了しました")


# ===============================
# 実行
# ===============================
if __name__ == "__main__":
    main()
