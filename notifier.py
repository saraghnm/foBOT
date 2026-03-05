# notifier.py

import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID


def notify(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        })
    except Exception as e:
        print(f"Telegram error: {e}")