import time

class MovingAverageCrossStrategy:
    def __init__(self, fast_period: int = 5, slow_period: int = 20):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.prices = {}
        self.prev_diff = {}

    async def check(self, exchange, symbol, old, current):
        key = (exchange, symbol)
        self.prices.setdefault(key, []).append(current)
        if len(self.prices[key]) < self.slow_period:
            return []
        prices = self.prices[key][-self.slow_period:]
        fast_ma = sum(prices[-self.fast_period:]) / self.fast_period
        slow_ma = sum(prices) / self.slow_period
        diff = fast_ma - slow_ma

        prev = self.prev_diff.get(key)
        self.prev_diff[key] = diff

        alerts = []
        if prev is not None:
            if prev < 0 and diff > 0:
                # Пересечение вверх (бычий сигнал)
                alerts.append({
                    "exchange": exchange,
                    "symbol": symbol,
                    "old": old,
                    "new": current,
                    "diff": abs(diff),
                    "direction": "📈 Пересечение вверх: fast MA выше slow MA",
                    "strategy": "MovingAverageCrossStrategy",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                })
            elif prev > 0 and diff < 0:
                # Пересечение вниз (медвежий сигнал)
                alerts.append({
                    "exchange": exchange,
                    "symbol": symbol,
                    "old": old,
                    "new": current,
                    "diff": abs(diff),
                    "direction": "📉 Пересечение вниз: fast MA ниже slow MA",
                    "strategy": "MovingAverageCrossStrategy",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                })
        return alerts