from sqlalchemy import select

from db.sqlite_module import DBManager, Order


async def calculate_balance_from_orders(
    db: DBManager,
    current_prices: dict[str, float],
    initial_cash: float = 1000.0
) -> tuple[float, float, dict, float, float]:
    """
    Подсчёт кэша, полной стоимости, портфеля, нереализованного и реализованного PnL.

    :return: (cash, total_equity, portfolio, unrealized_pnl, realized_pnl)
    """
    cash = initial_cash
    commission_rate = 0.001
    portfolio = {}
    realized_pnl = 0.0

    orders = await db.session.execute(
        select(Order).where(Order.status == "closed").order_by(Order.created_at)
    )
    orders = orders.scalars().all()

    for order in orders:
        symbol = order.symbol
        price = order.price or 0.0
        amount = order.amount
        side = order.side

        if side == "buy":
            cost = price * (1 + commission_rate) * amount
            cash -= cost

            if symbol not in portfolio:
                portfolio[symbol] = {"amount": amount, "avg_price": price}
            else:
                pos = portfolio[symbol]
                if pos["amount"] >= 0:
                    # Лонг → усреднение
                    total = pos["amount"] + amount
                    avg_price = (pos["avg_price"] * pos["amount"] + price * amount) / total
                    pos["amount"] = total
                    pos["avg_price"] = avg_price
                else:
                    # Покупка закрывает шорт
                    closing_amount = min(amount, abs(pos["amount"]))
                    pnl = (pos["avg_price"] - price) * closing_amount
                    realized_pnl += pnl
                    pos["amount"] += amount  # меньше отрицательное значение

                    if pos["amount"] > 0:
                        # Остаток в лонг
                        portfolio[symbol] = {"amount": pos["amount"], "avg_price": price}
                    elif pos["amount"] == 0:
                        del portfolio[symbol]

        elif side == "sell":
            revenue = price * (1 - commission_rate) * amount
            cash += revenue

            if symbol not in portfolio:
                # Новый шорт
                portfolio[symbol] = {"amount": -amount, "avg_price": price}
            else:
                pos = portfolio[symbol]
                if pos["amount"] > 0:
                    # Продажа закрывает лонг
                    closing_amount = min(amount, pos["amount"])
                    pnl = (price - pos["avg_price"]) * closing_amount
                    realized_pnl += pnl
                    pos["amount"] -= amount

                    if pos["amount"] < 0:
                        # Остаток уходит в шорт
                        short_amount = -pos["amount"]
                        portfolio[symbol] = {"amount": -short_amount, "avg_price": price}
                    elif pos["amount"] == 0:
                        del portfolio[symbol]

                else:
                    # Продажа расширяет шорт
                    total = abs(pos["amount"]) + amount
                    avg_price = (pos["avg_price"] * abs(pos["amount"]) + price * amount) / total
                    pos["amount"] -= amount
                    pos["avg_price"] = avg_price

    # Подсчёт нереализованного PnL и стоимости портфеля
    unrealized_pnl = 0.0
    portfolio_value = 0.0

    for symbol, pos in portfolio.items():
        current_price = current_prices.get(symbol)
        if current_price is None:
            continue

        amt = pos["amount"]
        avg_price = pos["avg_price"]
        portfolio_value += amt * current_price

        if amt > 0:
            unrealized_pnl += (current_price - avg_price) * amt
        else:
            unrealized_pnl += (avg_price - current_price) * abs(amt)

    total_equity = cash + portfolio_value

    return cash, total_equity, portfolio, unrealized_pnl, realized_pnl
