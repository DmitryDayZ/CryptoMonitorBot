import asyncio
import logging
from config import TRACKING, POLL_INTERVAL, THRESHOLD_PERCENT
from exchanges.ccxt_client import ExchangeManager
from telegram_bot import send_price_alert

# Настройка логирования: вывод в консоль, уровень INFO
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

last_prices = {}  # Словарь для хранения последних цен по каждой паре и бирже
ex = ExchangeManager()  # Менеджер для работы с биржами через ccxt

async def check_prices():
    """Асинхронный цикл, который периодически проверяет цены на биржах и отправляет уведомления при значительных изменениях."""
    global last_prices
    while True:
        for exchange, symbols in TRACKING.items():
            for symbol in symbols:
                try:
                    # Получаем текущую цену по бирже и символу
                    current = ex.fetch_price(exchange, symbol)
                    key = f"{exchange}_{symbol}"  # Уникальный ключ для хранения цены

                    if key in last_prices:
                        old = last_prices[key]
                        # Вычисляем процент изменения цены
                        diff = abs(current - old) / old * 100
                        # Определяем направление изменения
                        direction = "📈 выросла" if current > old else "📉 упала"

                        # Если изменение выше порога, отправляем уведомление
                        if diff >= THRESHOLD_PERCENT:
                            logging.info(f"Цена на {exchange} {symbol} {direction}: старое {old}, новое {current}, изменение {diff:.2f}%")
                            await send_price_alert(exchange, symbol, old, current, diff, direction)
                            last_prices[key] = current  # Обновляем цену
                        else:
                            # await send_price_alert(exchange, symbol, old, current, diff, direction)
                            logging.info(f"Изменение цены на {exchange} {symbol} меньше порога: {diff:.2f}%")
                    else:
                        # Если цены не было, просто записываем текущую
                        logging.info(f"Устанавливаем начальную цену для {exchange} {symbol}: {current}")
                        last_prices[key] = current  # Устанавливаем первую цену


                except Exception as e:
                    logging.error(f"Ошибка при получении цены {exchange} {symbol}: {e}")

        logging.info(f"Завершен цикл проверки. Ожидание {POLL_INTERVAL} секунд...")
        await asyncio.sleep(POLL_INTERVAL)
