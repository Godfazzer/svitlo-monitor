import os, requests, json, time

URLS = {
    "4.2": "https://be-svitlo.oe.if.ua/schedule-by-queue?queue=4.2",
    "3.2": "https://be-svitlo.oe.if.ua/schedule-by-queue?queue=3.2",
    "fake": "http://fake-svitlo-api:8000/schedule-by-queue?queue=fake"
}

QUEUE_NAMES = {
    "4.2": "Гузара",
    "3.2": "Ленкавського",
    "fake": "ТЕСТОВА Черга"
}

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "300"))
CACHE_DIR = "cache"


def send_telegram(text):
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"},
            timeout=10
        )
        if resp.status_code != 200:
            print(f"Telegram error {resp.status_code}: {resp.text}")
        else:
            print("Telegram message was sent")
    except Exception as e:
        print("Telegram send error:", e)


def fetch_schedule(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
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


def extract_relevant(schedule, queue):
    result = []
    for day in schedule:
        date = day.get("eventDate")
        qdata = day.get("queues", {}).get(queue, [])
        hours = [x.get("shutdownHours") for x in qdata]
        result.append({"date": date, "hours": hours})
    return result


def check_and_alert(queue, url):
    try:
        current = fetch_schedule(url)
        current_relevant = extract_relevant(current, queue)
        last_relevant = extract_relevant(load_last(queue) or [], queue)

        if last_relevant != current_relevant:
            if not current:
                # if API lisr is empty []
                parts = [
                    f"*Дата:* ?\n*Оновлено:* ?\n*Відключення:*\n✅ Немає відключень"
                ]
            else:
                parts = []
                for day in current:
                    date = day.get("eventDate", "?")
                    updated = day.get("scheduleApprovedSince", "?")
                    qdata = day.get("queues", {}).get(queue, [])
                    if qdata:
                        outages = "\n".join(
                            [f"🕒 {x.get('shutdownHours', '?')}" for x in qdata]
                        )
                    else:
                        outages = "✅ Немає відключень"
                    parts.append(
                        f"*Дата:* {date}\n*Оновлено:* {updated}\n*Відключення:*\n{outages}"
                    )

            display_name = QUEUE_NAMES.get(queue)
            queue_label = f"{queue} ({display_name})" if display_name else queue

            message = (
                f"⚡ *Змінився графік відключень!* 🟡\n"
                f"*Черга:* {queue_label}\n\n"
                + "\n\n".join(parts)
            )

            send_telegram(message)
            save_current(queue, current)
            print(f"[{queue}] Change in shutdown hours → message sent.")
        else:
            print(f"[{queue}] No change in shutdown hours.")
    except Exception as e:
        print(f"[{queue}] Error: {e}")


def main():
    send_telegram("🟢 Svitlo-monitor запущено.")
    while True:
        for queue, url in URLS.items():
            check_and_alert(queue, url)
            time.sleep(5)
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
