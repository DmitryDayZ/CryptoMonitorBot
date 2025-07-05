class MovingAverageCrossStrategy:
    def __init__(self, fast_period: int = 5, slow_period: int = 20):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.prices = {}

    async def check(self, exchange, symbol, old, current):
        key = (exchange, symbol)
        self.prices.setdefault(key, []).append(current)
        if len(self.prices[key]) < self.slow_period:
            return []
        prices = self.prices[key][-self.slow_period:]
        fast_ma = sum(prices[-self.fast_period:]) / self.fast_period
        slow_ma = sum(prices) / self.slow_period
        # Можно добавить логику пересечения
        return []