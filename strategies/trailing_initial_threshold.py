class TrailingInitialThresholdStrategy:
    def __init__(self, threshold_percent: float):
        self.threshold_percent = threshold_percent
        self.anchor_price: dict[str, float] = {}  # Якорь: отслеживаемая цена (минимум при покупке, максимум при продаже)
        self.direction: dict[str, str] = {}       # Направление последнего действия: 'buy', 'sell', 'neutral'

    async def check(self, exchange: str, symbol: str, current_price: float) -> list[dict]:
        alerts = []

        # Если символ новый, инициализируем
        if symbol not in self.anchor_price:
            self.anchor_price[symbol] = current_price
            self.direction[symbol] = 'neutral'
            return []

        anchor = self.anchor_price[symbol]
        direction = self.direction[symbol]

        # Изменение цены относительно якорной в процентах
        change = (current_price - anchor) / anchor * 100



        # 🎯 Сигнал на покупку: цена упала на threshold% от anchor
        if change <= -self.threshold_percent:
            alerts.append({
                "action": "buy",
                "strategy": f"TrailingInitialThresholdStrategy ({self.threshold_percent}%)",
                "amount": None  # пусть вызывающий код сам определит объём
            })
            # Обновляем якорь и направление
            self.anchor_price[symbol] = current_price
            self.direction[symbol] = 'buy'

        # 🎯 Сигнал на продажу: цена выросла на threshold% от anchor
        elif change >= self.threshold_percent:
            alerts.append({
                "action": "sell",
                "strategy": f"TrailingInitialThresholdStrategy ({self.threshold_percent}%)",
                "amount": None
            })
            self.anchor_price[symbol] = current_price
            self.direction[symbol] = 'sell'

        else:
            # Если ещё нет действия, просто обновляем anchor текущей ценой
            if direction == 'neutral':
                self.anchor_price[symbol] = current_price

            # Если ранее был buy, ищем новое дно для trailing-покупки
            elif direction == 'buy':
                self.anchor_price[symbol] = min(anchor, current_price)

            # Если ранее был sell, ищем новый максимум для trailing-продажи
            elif direction == 'sell':
                self.anchor_price[symbol] = max(anchor, current_price)

        return alerts
