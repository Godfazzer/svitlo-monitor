import os
import requests
import json
import time

URLS = {
    "4.2": "https://be-svitlo.oe.if.ua/schedule-by-queue?queue=4.2",
    "5.2": "https://be-svitlo.oe.if.ua/schedule-by-queue?queue=5.2",
    "3.2": "https://be-svitlo.oe.if.ua/schedule-by-queue?queue=3.2"
}

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "300"))
CACHE_DIR = "cache"

def send_telegram(text):
    """Send Telegram message with error logging."""
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text},
            timeout=10
        )
        if resp.status_code != 200:
            print(f"Telegram error {resp.status_code}: {resp.text}")
        else:
            print("Telegram message sent successfully.")
    except Exception as e:
        print("Telegram send error:", e)

def fetch_schedule(url):
    """Fetch JSON schedule from the given URL with headers."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://be-svitlo.oe.if.ua/",
        "Origin": "https://be-svitlo.oe.if.ua"
    }
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()

def load_last(queue):
    path = f"{CACHE_DIR}/{queue}.json"
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None

def save_current(queue, data):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(f"{CACHE_DIR}/{queue}.json", "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def check_and_alert(queue, url):
    try:
        current = fetch_schedule(url)
        last = load_last(queue)

        if last != current:
            message = f"⚡ Svitlo schedule updated for queue {queue}!\n\n{json.dumps(current, ensure_ascii=False, indent=2)}"
            send_telegram(message)
            save_current(queue, current)
            print(f"[{queue}] Change detected → message sent.")
        else:
            print(f"[{queue}] No change.")
    except Exception as e:
        print(f"[{queue}] Error: {e}")

def main():
    send_telegram("🟢 Svitlo monitor started.")
    while True:
        for queue, url in URLS.items():
            check_and_alert(queue, url)
            time.sleep(5)
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()