import os
from dotenv import load_dotenv

load_dotenv()  # Загружает переменные из .env

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 60))

TRACKING = {
    # "binance": ["TON/USDT"],
    "binance": ["TON/USDT","NOT/USDT","BTC/USDT","ETH/USDT","XRP/USDT","SOL/USDT"],
    "bybit": ["TON/USDT", "NOT/USDT", "BTC/USDT", "ETH/USDT", "XRP/USDT", "SOL/USDT"],
}