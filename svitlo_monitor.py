import os, requests, json, time
from datetime import datetime

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


# =====================
# TELEGRAM SENDER
# =====================
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


# =====================
# API FETCHER (Protected against Cloudflare)
# =====================
def fetch_schedule(url):
    headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "C",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": (
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/16.0 Safari/605.1.15 Midori/6"
    ),
    "Connection": "keep-alive",
    "Host": "be-svitlo.oe.if.ua",   # override target host
    }


    try:
        r = requests.get(url, headers=headers, timeout=10)
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")
        return None

    # Cloudflare blocks → 403 / 503
    if r.status_code in (403, 503):
        print(f"[CF BLOCK] HTTP {r.status_code} from {url}")
        return None

    # Cloudflare returns HTML instead of JSON
    content_type = r.headers.get("Content-Type", "")
    if "application/json" not in content_type:
        preview = r.text[:200].replace("\n", " ")
        print(f"[CF BLOCK] Non-JSON response: {preview}")
        return None

    try:
        return r.json()
    except Exception:
        print(f"[CF BLOCK] JSON decode failed. First 200 chars: {r.text[:200]}")
        return None


# =====================
# CACHE HANDLING
# =====================
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


# =====================
# SIMPLIFY SCHEDULE DATA
# =====================
def extract_relevant(schedule, queue):
    result = {}
    today = datetime.now().date()

    for day in schedule or []:
        date_str = day.get("eventDate")
        try:
            date_obj = datetime.strptime(date_str, "%d.%m.%Y").date()
        except Exception:
            continue

        if date_obj < today:
            continue

        qdata = day.get("queues", {}).get(queue, [])
        simplified = [
            {
                "shutdownHours": x.get("shutdownHours"),
                "from": x.get("from"),
                "to": x.get("to"),
                "status": x.get("status"),
            }
            for x in qdata
        ]

        result[date_str] = simplified

    return result


# =====================
# MAIN CHECK FUNCTION
# =====================
def check_and_alert(queue, url):
    try:
        # Retry on Cloudflare failure
        current = None
        for attempt in range(3):
            current = fetch_schedule(url)
            if current is not None:
                break
            print(f"[{queue}] Retry {attempt+1}/3 after CF block...")
            time.sleep(2)

        if current is None:
            print(f"[{queue}] Giving up after Cloudflare blocks.")
            return

        last = load_last(queue) or []

        current_relevant = extract_relevant(current, queue)
        last_relevant = extract_relevant(last, queue)

        # --- FIX: Remove past days from last_relevant BEFORE comparing ---
        last_relevant = {
            d: v for d, v in last_relevant.items()
            if datetime.strptime(d, "%d.%m.%Y").date() >= datetime.now().date()
        }
        # --

        today = datetime.now().strftime("%d.%m.%Y")
        last_dates = [d.get("eventDate") for d in (last or [])]

        last_only_past = all(
            datetime.strptime(d, "%d.%m.%Y").date() < datetime.now().date()
            for d in last_dates if d
        )

        # NEW DAY & empty schedule (ignore)
        if not current and last_only_past:
            print(f"[{queue}] Empty schedule at new day start → ignored.")
            save_current(queue, current)
            return

        # Cancelled schedule
        if not current and not last_only_past:
            display_name = QUEUE_NAMES.get(queue)
            queue_label = f"{queue} ({display_name})"
            message = (
                f"⚡ *Графік скасовано!* 🟢\n"
                f"*Черга:* {queue_label}\n\n"
                f"*Дата:* {today}\n"
                f"*Відключення:* ✅ Немає відключень"
            )
            send_telegram(message)
            save_current(queue, current)
            print(f"[{queue}] Schedule cancelled → message sent.")
            return

        # Changes detected (including new day)
        if current_relevant != last_relevant:
            parts = []
            for day in current:
                date = day.get("eventDate", "?")
                updated = day.get("scheduleApprovedSince", "?")
                qdata = day.get("queues", {}).get(queue, [])
                if qdata:
                    outages = "\n".join(
                        [f"🕒 {x.get('from', '?')} - {x.get('to', '?')}" for x in qdata]
                    )
                else:
                    outages = "✅ Немає відключень"
                parts.append(
                    f"*Дата:* {date}\n*Оновлено:* {updated}\n*Відключення:*\n{outages}"
                )

            queue_label = f"{queue} ({QUEUE_NAMES.get(queue)})"
            message = (
                f"⚡ *Змінився графік відключень!* 🟡\n"
                f"*Черга:* {queue_label}\n\n"
                + "\n\n".join(parts)
            )
            send_telegram(message)
            save_current(queue, current)
            print(f"[{queue}] Change detected → message sent.")
        else:
            print(f"[{queue}] No change in shutdown hours.")

    except Exception as e:
        print(f"[{queue}] Error: {e}")


# =====================
# MAIN LOOP
# =====================
def main():
    time.sleep(3)
    print("🟢 Svitlo-monitor started.")

    while True:
        for queue, url in URLS.items():
            check_and_alert(queue, url)
            time.sleep(5)

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
