class StaticInitialThresholdStrategy:
    def __init__(self, threshold_percent: float):
        self.threshold_percent = threshold_percent
        self.initial_price: dict[str, float] = {}

    async def check(self, exchange: str, symbol: str, current_price: float) -> list[dict]:
        alerts = []

        # Устанавливаем начальную цену один раз
        if symbol not in self.initial_price:
            self.initial_price[symbol] = current_price
            return []

        start_price = self.initial_price[symbol]
        change = (current_price - start_price) / start_price * 100

        # Если цена упала на threshold% — покупаем
        if change <= -self.threshold_percent:
            alerts.append({
                "action": "buy",
                "strategy": f"StaticInitialThresholdStrategy ({self.threshold_percent}%)",
                "amount": None
            })

        # Если цена выросла на threshold% — продаём
        elif change >= self.threshold_percent:
            alerts.append({
                "action": "sell",
                "strategy": f"StaticInitialThresholdStrategy ({self.threshold_percent}%)",
                "amount": None
            })

        return alerts
