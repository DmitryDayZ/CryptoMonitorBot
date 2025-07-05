import logging
import time

class InitialThresholdStrategy:
    def __init__(self, threshold_percent: float):
        self.threshold_percent = threshold_percent
        self.initial_prices = {}

    async def check(self, exchange, symbol, current):
        key = (exchange, symbol)
        if key not in self.initial_prices:
            self.initial_prices[key] = current
            return []
        initial = self.initial_prices[key]
        if initial == 0:
            return []
        diff = abs(current - initial) / initial * 100
        logging.info(f"InitialThresholdStrategy: изменение {diff:.2f}% для {exchange} {symbol}")
        if diff >= self.threshold_percent:
            direction = "📈 выросла" if current > initial else "📉 упала"
            return [{
                "exchange": exchange,
                "pair": symbol,
                "old": initial,
                "new": current,
                "diff": diff,
                "direction": direction,
                "strategy": "InitialThresholdStrategy",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }]
        return []