import asyncio
import logging
from config import TRACKING, POLL_INTERVAL, THRESHOLD_PERCENT
from exchanges.ccxt_client import ExchangeManager
from strategies.volume_spikes import VolumeSpikeStrategy
from telegram_bot import send_price_alert
from strategies.threshold import ThresholdStrategy


# Настройка логирования: вывод в консоль, уровень INFO
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

last_prices = {}  # Словарь для хранения последних цен по каждой паре и бирже
ex = ExchangeManager()  # Менеджер для работы с биржами через ccxt

strategies = [
    ThresholdStrategy(THRESHOLD_PERCENT),
    VolumeSpikeStrategy(spike_percent=1),  # например, 50%
    # другие стратегии
]

async def check_prices():
    global last_prices
    while True:
        for exchange, symbols in TRACKING.items():
            for symbol in symbols:
                try:
                    ticker = ex.exchanges[exchange].fetch_ticker(symbol)
                    current = ticker['last']
                    volume = ticker.get('baseVolume', 0)
                    key = f"{exchange}_{symbol}"
                    old = last_prices.get(key)
                    for strategy in strategies:
                        if isinstance(strategy, VolumeSpikeStrategy):
                            alerts = await strategy.check(exchange, symbol, old, current, volume)
                        else:
                            alerts = await strategy.check(exchange, symbol, old, current)
                        for alert in alerts:
                            await send_price_alert(**alert)
                    last_prices[key] = current
                except Exception as e:
                    logging.error(f"Ошибка при получении цены {exchange} {symbol}: {e}")
        logging.info(f"Завершен цикл проверки. Ожидание {POLL_INTERVAL} секунд...")
        await asyncio.sleep(POLL_INTERVAL)