
class ThresholdStrategy:
    def __init__(self, threshold_percent: float):
        self.threshold_percent = threshold_percent

    async def check(self, exchange, symbol, old, current):
        if old is None:
            return []
        diff = abs(current - old) / old * 100
        if diff >= self.threshold_percent:
            direction = "📈 выросла" if current > old else "📉 упала"
            return [{
                "exchange": exchange,
                "pair": symbol,
                "old": old,
                "new": current,
                "diff": diff,
                "direction": direction
            }]
        return []