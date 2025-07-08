import time

class MartingaleStrategy:
    def __init__(self, threshold_percent=1.0, max_steps=5, initial_amount=10):
        self.threshold_percent = threshold_percent
        self.max_steps = max_steps
        self.initial_amount = initial_amount
        self.positions = {}  # {(exchange, symbol): {"entry": price, "step": int, "amount": float}}

    async def check(self, exchange: str, symbol: str, current_price: float):
        key = (exchange, symbol)
        action = "none"
        alerts = []

        position = self.positions.get(key)

        if not position:
            # первая покупка
            self.positions[key] = {
                "entry": current_price,
                "step": 0,
                "amount": self.initial_amount,
                "direction": "buy"
            }
            return []

        entry_price = position["entry"]
        step = position["step"]
        total_amount = position["amount"]
        direction = position["direction"]

        drop_percent = ((entry_price - current_price) / entry_price) * 100

        # усреднение при падении
        if drop_percent >= self.threshold_percent and step < self.max_steps:
            amount = self.initial_amount * (2 ** step)

            # пересчёт средней цены входа
            new_total_amount = total_amount + amount
            new_avg_price = (entry_price * total_amount + current_price * amount) / new_total_amount

            self.positions[key] = {
                "entry": new_avg_price,
                "step": step + 1,
                "amount": new_total_amount,
                "direction": "buy"
            }

            alerts.append({
                "exchange": exchange,
                "pair": symbol,
                "old": entry_price,
                "new": current_price,
                "diff": drop_percent,
                "direction": "📉 усреднение",
                "strategy": f"Martingale ({self.threshold_percent}% step, {step+1}/{self.max_steps})",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "action": "buy",
                "amount": amount,
                "avg_price": new_avg_price,
                "step": step + 1,
            })

        # выход из позиции при росте выше avg_price на threshold_percent
        elif current_price > entry_price * (1 + self.threshold_percent / 100):
            alerts.append({
                "exchange": exchange,
                "pair": symbol,
                "old": entry_price,
                "new": current_price,
                "diff": ((current_price - entry_price) / entry_price) * 100,
                "direction": "📈 откат вверх",
                "strategy": f"Martingale EXIT",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "action": "sell",
                "amount": total_amount,
                "avg_price": entry_price,
                "step": step,
            })

            del self.positions[key]

        return alerts
