import logging
from datetime import datetime

from db.sqlite_module import DBManager, AsyncSessionLocal
from services.history import load_all_data_to_dataframe
from strategies.initial_threshold import InitialThresholdStrategy
from strategies.trailing_initial_threshold import TrailingInitialThresholdStrategy
from tgbot.config import COIN_NAME, POSITION_SIZE

import numpy as np


async def optimize_threshold(db: DBManager, percent_range=(0.5, 5.0), step=0.5):
    results = []

    for percent in [round(p, 2) for p in frange(percent_range[0], percent_range[1] + step, step)]:
        print(f"📊 Тестируем стратегию с порогом {percent}%")

        strategy = InitialThresholdStrategy(threshold_percent=percent)
        global strategies
        strategies = [strategy]

        # запуск эмуляции (она должна возвращать equity и PnL)
        cash, equity, portfolio, unrealized, realized = await emulate_prices_for_strategy()

        results.append({
            "threshold": percent,
            "equity": equity,
            "realized_pnl": realized,
            "unrealized_pnl": unrealized,
        })

    # сортировка по equity
    results.sort(key=lambda x: x["equity"], reverse=True)

    print("\n🏁 Топ результаты:")
    for r in results:
        print(f"{r['threshold']}% → 📈 Equity: {r['equity']:.2f} | 💵 Realized PnL: {r['realized_pnl']:.2f}")

    return results

def frange(start, stop, step):
    while start < stop:
        yield start
        start += step

async def emulate_prices_for_strategy() -> tuple[float, float, dict, float, float]:
    cash = 1_000.0
    commission_rate = 0.001
    portfolio = {}
    realized_pnl = 0.0

    start = datetime(2025, 7, 1)
    end = datetime(2025, 7, 6)

    df = load_all_data_to_dataframe(f"historydata/{COIN_NAME}", start, end)
    if df.empty:
        logging.error("Нет данных для эмуляции.")
        return 0.0, 0.0, {}, 0.0, 0.0
    symbol=COIN_NAME
    try:
        async with AsyncSessionLocal() as session:
            db = DBManager(session)

            for _, row in df.iterrows():
                    try:
                        date = row["datetime"]
                        close = row["close"]
                        volume = row["volume"]
                        current_prices = {symbol: close}





                        exchange = "binance"
                        current_prices = {symbol: close}

                        old_price = await db.get_last_price(exchange, symbol)
                        await db.save_price(exchange, symbol, close, volume)

                        for strategy in strategies:
                            alerts = await strategy.check(exchange, symbol, close)

                            for alert in alerts:
                                print(f'{alert["action"]} {date} O:{row["open"]} H:{row["high"]} L:{row["low"]} C:{row["close"]} V:{row["volume"]}' )
                                alert.setdefault("pair", symbol)
                                alert.setdefault("old", old_price)
                                alert.setdefault("new", close)
                                alert.setdefault("action", "none")
                                alert.setdefault("strategy", "unknown")

                                action = alert["action"]
                                strategy_name = alert["strategy"]
                                amount = alert.get("amount")
                                if amount is None:
                                    amount = POSITION_SIZE / close if POSITION_SIZE else 10 / close

                                # BUY
                                if action == "buy":
                                    trade_price = close * (1 + commission_rate)
                                    cost = trade_price * amount
                                    if cash >= cost:
                                        cash -= cost
                                        if symbol not in portfolio or portfolio[symbol]["amount"] <= 0:
                                            portfolio[symbol] = {"amount": amount, "avg_price": close}
                                        else:
                                            pos = portfolio[symbol]
                                            total = pos["amount"] + amount
                                            avg_price = (pos["avg_price"] * pos["amount"] + close * amount) / total
                                            portfolio[symbol] = {"amount": total, "avg_price": avg_price}

                                # SELL
                                elif action == "sell":
                                    trade_price = close * (1 - commission_rate)
                                    revenue = trade_price * amount
                                    cash += revenue

                                    if symbol in portfolio and portfolio[symbol]["amount"] > 0:
                                        pos = portfolio[symbol]
                                        closed_amount = min(pos["amount"], amount)
                                        pnl = (close - pos["avg_price"]) * closed_amount
                                        realized_pnl += pnl
                                        pos["amount"] -= closed_amount

                                        if pos["amount"] <= 0:
                                            del portfolio[symbol]

                    except Exception as e:
                        logging.error(f"Ошибка в свече: {e}")

        # Финальный расчёт equity
        final_price = close
        portfolio_value = sum(pos["amount"] * final_price for pos in portfolio.values())
        unrealized_pnl = sum((final_price - pos["avg_price"]) * pos["amount"] for pos in portfolio.values())
        equity = cash + portfolio_value

        return cash, equity, portfolio, unrealized_pnl, realized_pnl

    except Exception as e:
        logging.critical(f"Ошибка в emulate_prices_for_strategy: {e}")
        return 0.0, 0.0, {}, 0.0, 0.0



async def optimize_threshold():
    results = []

    for threshold in np.arange(0.5, 5.5, 0.5):  # от 0.5% до 5.0%
        print(f"\n🧪 Тестируем стратегию с порогом: {threshold:.1f}%")
        strategy = TrailingInitialThresholdStrategy(threshold_percent=threshold)
        global strategies
        strategies = [strategy]

        cash, equity, portfolio, unrealized, realized = await emulate_prices_for_strategy()

        results.append({
            "threshold": threshold,
            "equity": equity,
            "cash": cash,
            "realized": realized,
            "unrealized": unrealized
        })

    # Сортируем по equity (или можно по realized PnL)
    results.sort(key=lambda x: x["equity"], reverse=True)

    print("\n📊 Результаты оптимизации (по Equity):")
    for res in results:
        print(f"Threshold: {res['threshold']:.1f}% | Equity: {res['equity']:.2f} | Realized: {res['realized']:.2f} | Unrealized: {res['unrealized']:.2f}")

    best = results[0]
    print(f"\n✅ Лучший результат: {best['threshold']:.1f}% — Equity: {best['equity']:.2f} USDT")

    return best
