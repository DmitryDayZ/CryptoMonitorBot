import asyncio
import logging
from config import TRACKING, POLL_INTERVAL, THRESHOLD_PERCENT
from exchanges.ccxt_client import ExchangeManager
from telegram_bot import send_price_alert
from strategies.threshold import ThresholdStrategy


# Настройка логирования: вывод в консоль, уровень INFO
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

last_prices = {}  # Словарь для хранения последних цен по каждой паре и бирже
ex = ExchangeManager()  # Менеджер для работы с биржами через ccxt

strategies = [
    ThresholdStrategy(THRESHOLD_PERCENT),
    # Здесь можно добавить другие стратегии
]

async def check_prices():
    global last_prices
    while True:
        for exchange, symbols in TRACKING.items():
            for symbol in symbols:
                try:
                    current = ex.fetch_price(exchange, symbol)
                    key = f"{exchange}_{symbol}"
                    old = last_prices.get(key)
                    for strategy in strategies:
                        alerts = await strategy.check(exchange, symbol, old, current)
                        for alert in alerts:
                            await send_price_alert(**alert)
                    last_prices[key] = current
                except Exception as e:
                    logging.error(f"Ошибка при получении цены {exchange} {symbol}: {e}")
        logging.info(f"Завершен цикл проверки. Ожидание {POLL_INTERVAL} секунд...")
        await asyncio.sleep(POLL_INTERVAL)