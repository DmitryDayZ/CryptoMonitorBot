import logging
import time


class InitialThresholdStrategy:
    def __init__(self, threshold_percent: float):
        """
        :param threshold_percent: Порог изменения цены в процентах, при достижении которого срабатывает стратегия.
        """
        self.threshold_percent = threshold_percent
        self.initial_prices = {}  # Словарь для хранения начальных цен { (exchange, symbol): price }

    async def check(self, exchange, symbol, current):
        """
        Проверка, изменилась ли цена достаточно сильно с начального значения.

        :param exchange: Название биржи (например, 'binance')
        :param symbol: Торговая пара (например, 'BTC/USDT')
        :param current: Текущая цена актива
        :return: Список алертов (если есть), иначе пустой список
        """
        key = (exchange, symbol)

        # Если начальная цена ещё не установлена — сохраняем и ничего не возвращаем
        if key not in self.initial_prices:
            self.initial_prices[key] = {"price":current,"up_checked": False, "down_checked":False}
            return []
        action= "none"
        initial = self.initial_prices[key]["price"]
        up_checked = self.initial_prices[key]["up_checked"]
        down_checked = self.initial_prices[key]["down_checked"]

        # Защита от деления на ноль и двойного срабатывания стратегии
        if initial == 0 or (up_checked and down_checked):
            return []

        # Вычисляем процентное изменение от начальной цены
        diff = abs(current - initial) / initial * 100
        # logging.info(f"InitialThresholdStrategy: изменение {diff:.2f}% для {exchange} {symbol}")

        # Если изменение превышает заданный порог
        if diff >= self.threshold_percent:
            self.initial_prices[key] = {"price": current, "up_checked": False, "down_checked": False}
            if current > initial:
                direction = "📈 выросла"
                action = "sell"

            else:
                direction = "📉 упала"
                action = "buy"

            # Возвращаем словарь с данными об алерте
            return [{
                "exchange": exchange,
                "pair": symbol,
                "old": initial,
                "new": current,
                "diff": diff,
                "direction": direction,
                "strategy": f"InitialThresholdStrategy ({self.threshold_percent}%)",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "action": action,
            }]

        # Иначе изменений недостаточно — возвращаем пустой список
        return []

    async def check_old(self, exchange, symbol, current):
        """
        Проверка, изменилась ли цена достаточно сильно с начального значения.

        :param exchange: Название биржи (например, 'binance')
        :param symbol: Торговая пара (например, 'BTC/USDT')
        :param current: Текущая цена актива
        :return: Список алертов (если есть), иначе пустой список
        """
        key = (exchange, symbol)

        # Если начальная цена ещё не установлена — сохраняем и ничего не возвращаем
        if key not in self.initial_prices:
            self.initial_prices[key] = {"price":current,"up_checked": False, "down_checked":False}
            return []
        action= "none"
        initial = self.initial_prices[key]["price"]
        up_checked = self.initial_prices[key]["up_checked"]
        down_checked = self.initial_prices[key]["down_checked"]

        # Защита от деления на ноль и двойного срабатывания стратегии
        if initial == 0 or (up_checked and down_checked):
            return []

        # Вычисляем процентное изменение от начальной цены
        diff = abs(current - initial) / initial * 100
        # logging.info(f"InitialThresholdStrategy: изменение {diff:.2f}% для {exchange} {symbol}")

        # Если изменение превышает заданный порог
        if diff >= self.threshold_percent:
            if current > initial:
                direction = "📈 выросла"
                if not self.initial_prices[key]["up_checked"]:
                    self.initial_prices[key]["up_checked"] = True
                    action="sell"
            else:
                direction = "📉 упала"
                if not self.initial_prices[key]["down_checked"]:
                    self.initial_prices[key]["down_checked"] = True
                    action = "buy"

            # Возвращаем словарь с данными об алерте
            return [{
                "exchange": exchange,
                "pair": symbol,
                "old": initial,
                "new": current,
                "diff": diff,
                "direction": direction,
                "strategy": f"InitialThresholdStrategy ({self.threshold_percent}%)",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "action": action,
            }]

        # Иначе изменений недостаточно — возвращаем пустой список
        return []
