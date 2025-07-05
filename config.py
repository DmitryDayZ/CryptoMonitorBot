import os
from dotenv import load_dotenv

load_dotenv()  # Загружает переменные из .env

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 60))
THRESHOLD_PERCENT = float(os.getenv("THRESHOLD_PERCENT", 1.0))

TRACKING = {
    "binance": ["TON/USDT"],
}