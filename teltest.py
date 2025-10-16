import requests

BOT_TOKEN = "8083367699:AAGFS0dicva_OaYa-73gs4LtiobjMwgmYX4"
CHAT_ID = "-1002869926618"

r = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    json={"chat_id": CHAT_ID, "text": "Test message from Python"}
)
print(r.status_code, r.text)