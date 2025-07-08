import os
from dotenv import load_dotenv

load_dotenv()  # Загружает переменные из .env

DATABASE_URL = os.getenv("SQLITE_DB_PATH")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ADMIN_ID = int(os.getenv("ADMIN_ID", 740130054))  # ID администратора, по умолчанию 740130054
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 60))
POSITION_SIZE = float(os.getenv("POSITION_SIZE", 20))  # Размер позиции по умолчанию 20 USD
HISTORICAL_DATA_PATH = os.getenv("HISTORICAL_DATA_PATH")
COIN_NAME = os.getenv("COIN_NAME", "TON")  # Название монеты по умолчанию TON

TRACKING = {
    # "binance": ["TON/USDT","NOT/USDT"],

    "binance": ["TON/USDT","NOT/USDT","BTC/USDT","ETH/USDT","XRP/USDT","SOL/USDT"],
    # "bybit": ["TON/USDT", "NOT/USDT", "BTC/USDT", "ETH/USDT", "XRP/USDT", "SOL/USDT"],
}
