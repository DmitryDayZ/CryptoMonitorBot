import asyncio
import csv
import logging
import matplotlib.pyplot as plt
from datetime import datetime

from db.sqlite_module import DBManager, AsyncSessionLocal
from services.history import load_all_data_to_dataframe
from services.order_manager import OrderManager
from services.portfolio import calculate_balance_from_orders
from strategies.trailing_initial_threshold import TrailingInitialThresholdStrategy
from tgbot.config import TRACKING, ADMIN_ID, POLL_INTERVAL, POSITION_SIZE, TELEGRAM_CHAT_ID, HISTORICAL_DATA_PATH, \
    COIN_NAME
from tgbot.keyboards.inline import very_simple_keyboard
from exchanges.ccxt_client import ExchangeManager
from strategies.initial_threshold import InitialThresholdStrategy
from strategies.volume_spikes import VolumeSpikeStrategy
from tgbot.telegram_bot import send_price_alert, bot




ex = ExchangeManager()  # Обёртка над CCXT
strategies = [TrailingInitialThresholdStrategy(threshold_percent=0.5)]


order_manager = OrderManager()


async def check_prices():
    while True:
        try:
            async with AsyncSessionLocal() as session:
                db = DBManager(session)

                for exchange, symbols in TRACKING.items():
                    for symbol in symbols:
                        try:
                            ticker = await ex.exchanges[exchange].fetch_ticker(symbol)
                            current_price = ticker['last']
                            volume = ticker.get('baseVolume', 0)
                            old_price = await db.get_last_price(exchange, symbol)
                            await db.save_price(exchange, symbol, current_price, volume)

                            for strategy in strategies:
                                if isinstance(strategy, VolumeSpikeStrategy):
                                    pass
                                    # alerts = await strategy.check(exchange, symbol, old_price, current_price, volume)
                                else:
                                    alerts = await strategy.check(exchange, symbol, current_price)

                                for alert in alerts:
                                    # Приведение ключей к нужным для send_price_alert
                                    alert.setdefault("pair", alert.get("symbol", symbol))
                                    alert.setdefault("old", alert.get("old_price", old_price))
                                    alert.setdefault("new", alert.get("new_price", current_price))

                                    if alert.get("action") !="none":
                                        await send_price_alert(
                                            exchange=alert["exchange"],
                                            pair=alert["pair"],
                                            old=alert["old"],
                                            new=alert["new"],
                                            diff=alert.get("diff", 0),
                                            direction=alert.get("direction", ""),
                                            timestamp=alert.get("timestamp", ""),
                                            strategy=alert.get("strategy"),
                                        )

                                    amount = alert.get("amount", 10)
                                    amount = POSITION_SIZE if POSITION_SIZE else amount
                                    amount = amount/current_price

                                    if alert.get("action") == "buy":
                                        order = await order_manager.emulate_buy(exchange, symbol, amount, current_price)
                                        if order:
                                            await db.create_order(strategy=alert.get("strategy", "unknown"),exchange=exchange,symbol=symbol,order_type="market",side="buy",amount=amount,price=current_price,status="closed",order_id=None,)
                                            logging.info(f"Ордер покупку выполнен: {order}")
                                            text=f"🟢 Открываю лонг на {POSITION_SIZE}$ \n{symbol} на {exchange} по цене {current_price}\n"
                                            await bot.send_message(TELEGRAM_CHAT_ID, text=text, reply_markup=very_simple_keyboard())
                                        else:
                                            logging.error(
                                                f"Не удалось создать ордер покупку для {symbol} на {exchange}")

                                    if alert.get("action") == "sell":
                                        order = await order_manager.emulate_sell(exchange, symbol, amount,current_price)
                                        if order:
                                            await db.create_order(strategy=alert.get("strategy", "unknown"),exchange=exchange,symbol=symbol,order_type="market",side="sell",amount=amount,price=current_price,status="closed",order_id=None,)
                                            logging.info(f"Ордер продажу выполнен: {order}")
                                            text = f"🔴 Открываю шорт на {POSITION_SIZE}$ \n{symbol} на {exchange} по цене {current_price}\n"
                                            await bot.send_message(TELEGRAM_CHAT_ID, text=text, reply_markup=very_simple_keyboard())
                                        else:
                                            logging.error(
                                                f"Не удалось создать ордер продажу для {symbol} на {exchange}")

                        except Exception as e:
                            logging.error(f"[{exchange} {symbol}] Ошибка: {e}")

            logging.info(f"Цикл завершён, спим {POLL_INTERVAL} сек...\n")
            await asyncio.sleep(POLL_INTERVAL)

        except Exception as e:
            logging.critical(f"Глобальная ошибка в check_prices: {e}")
            await asyncio.sleep(POLL_INTERVAL)
        finally:
            await ex.close_all()  # <-- Закрываем соединения CCXT


def plot_pnl_history(timestamps, realized, unrealized, equity):
    plt.figure(figsize=(12, 6))
    plt.plot(timestamps, realized, label="💵 Реализованный PnL", color="green")
    plt.plot(timestamps, unrealized, label="📉 Нереализованный PnL", color="orange")
    plt.plot(timestamps, equity, label="📈 Общий Equity", color="blue")
    plt.title("Динамика портфеля")
    plt.xlabel("Время")
    plt.ylabel("USDT")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


async def emulate_trade():
    cash = 1_000.0
    commission_rate = 0.001
    portfolio = {}
    realized_pnl = 0.0

    # Истории
    timestamps = []
    equity_history = []
    realized_pnl_history = []
    unrealized_pnl_history = []

    start = datetime(2025, 7, 1)
    end = datetime(2025, 7, 6)

    df = load_all_data_to_dataframe(f"historydata/{COIN_NAME}", start, end)
    if df.empty:
        logging.error("Нет данных для эмуляции.")
        return 0.0, 0.0, {}, 0.0, 0.0
    symbol = COIN_NAME
    try:
        async with AsyncSessionLocal() as session:
            db = DBManager(session)
            await db.delete_all_orders()

            for _, row in df.iterrows():
                try:
                    date = row["datetime"]
                    close = row["close"]
                    volume = row["volume"]
                    current_prices = {symbol: close}
                    exchange = "binance"

                    old_price = await db.get_last_price(exchange, symbol)
                    await db.save_price(exchange, symbol, close, volume)

                    for strategy in strategies:
                        alerts = await strategy.check(exchange, symbol, close)

                        for alert in alerts:
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

                            step = alert.get("step")

                            if action == "buy":
                                print(f"{date} BUY {amount} {symbol} at {close}")
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
                                    created_at = date
                                    await db.create_order(strategy_name, exchange, symbol, "market", "buy", amount,
                                                          close, "closed", None, created_at=created_at)
                                    cash, equity, portfolio, unrealized, realized = await calculate_balance_from_orders(
                                        db, current_prices)
                                    print(f"💰 Кэш: {cash:.2f} USDT")
                                    print(f"📈 Активы (Equity): {equity:.2f} USDT")
                                    print(f"📦 Портфель: {portfolio}")
                                    print(f"📉 Нереализованный PnL: {unrealized:.2f} USDT")
                                    print(f"💵 Реализованный PnL: {realized:.2f} USDT")

                            elif action == "sell":
                                print(f"{date} SELL {amount} {symbol} at {close}")
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
                                created_at = date
                                await db.create_order(strategy_name, exchange, symbol, "market", "sell", amount, close,
                                                      "closed", None, created_at=created_at)
                                cash, equity, portfolio, unrealized, realized = await calculate_balance_from_orders(
                                    db, current_prices)
                                print(f"💰 Кэш: {cash:.2f} USDT")
                                print(f"📈 Активы (Equity): {equity:.2f} USDT")
                                print(f"📦 Портфель: {portfolio}")
                                print(f"📉 Нереализованный PnL: {unrealized:.2f} USDT")
                                print(f"💵 Реализованный PnL: {realized:.2f} USDT")

                    # 💾 Сохраняем значения для графика
                    portfolio_value = sum(
                        pos["amount"] * close for pos in portfolio.values()
                    )
                    unrealized_pnl = sum(
                        (close - pos["avg_price"]) * pos["amount"]
                        for pos in portfolio.values()
                    )
                    equity = cash + portfolio_value

                    timestamps.append(date)
                    realized_pnl_history.append(realized_pnl)
                    unrealized_pnl_history.append(unrealized_pnl)
                    equity_history.append(equity)

                except Exception as e:
                    logging.error(f"Ошибка в свече: {e}")

        logging.info(f"Эмуляция завершена. Итоговый баланс: {cash:.2f} USDT")

        cash, equity, portfolio, unrealized, realized = await calculate_balance_from_orders(db, current_prices)
        print(f"💰 Кэш: {cash:.2f} USDT")
        print(f"📈 Активы (Equity): {equity:.2f} USDT")
        print(f"📦 Портфель: {portfolio}")
        print(f"📉 Нереализованный PnL: {unrealized:.2f} USDT")
        print(f"💵 Реализованный PnL: {realized:.2f} USDT")


    except Exception as e:
        logging.critical(f"Ошибка в emulate_prices: {e}")


async def emulate_prices():
    cash = 1_000.0
    commission_rate = 0.001
    portfolio = {}
    realized_pnl = 0.0

    # Истории
    timestamps = []
    equity_history = []
    realized_pnl_history = []
    unrealized_pnl_history = []

    try:
        async with AsyncSessionLocal() as session:
            db = DBManager(session)

            with open(HISTORICAL_DATA_PATH, "r") as f:
                reader = csv.reader(f)
                for row in reader:
                    try:
                        ts = int(row[0])
                        date = datetime.fromtimestamp(ts / 1_000_000)
                        date_str = date.strftime('%Y-%m-%d %H:%M:%S')
                        close = float(row[4])
                        volume = float(row[5])
                        symbol = HISTORICAL_DATA_PATH.replace(".csv", "")
                        exchange = "binance"
                        current_prices = {symbol: close}

                        old_price = await db.get_last_price(exchange, symbol)
                        await db.save_price(exchange, symbol, close, volume)

                        for strategy in strategies:
                            alerts = await strategy.check(exchange, symbol, close)

                            for alert in alerts:
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

                                created_at = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

                                if action == "buy":
                                    print(f"{date_str} BUY {amount:.6f} {symbol} at {close:.2f}")
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

                                        await db.create_order(strategy_name, exchange, symbol, "market", "buy",
                                                              amount, close, "closed", None, created_at=created_at)

                                elif action == "sell":
                                    if symbol in portfolio and portfolio[symbol]["amount"] > 0:
                                        pos = portfolio[symbol]
                                        closed_amount = min(pos["amount"], amount)
                                        estimated_pnl = (close - pos["avg_price"]) * closed_amount

                                        # 💡 Фильтрация: пропускаем, если PnL отрицательный
                                        if estimated_pnl < 0:
                                            print(f"{date_str} ❌ SKIP SELL {symbol} — PnL: {estimated_pnl:.2f} USDT < 0")
                                            continue

                                        print(f"{date_str} SELL {amount:.6f} {symbol} at {close:.2f}")
                                        trade_price = close * (1 - commission_rate)
                                        revenue = trade_price * amount
                                        cash += revenue

                                        realized_pnl += estimated_pnl
                                        pos["amount"] -= closed_amount

                                        if pos["amount"] <= 0:
                                            del portfolio[symbol]

                                        await db.create_order(strategy_name, exchange, symbol, "market", "sell",
                                                              amount, close, "closed", None, created_at=created_at)

                        # 💾 Сохраняем значения для графика
                        portfolio_value = sum(pos["amount"] * close for pos in portfolio.values())
                        unrealized_pnl = sum(
                            (close - pos["avg_price"]) * pos["amount"]
                            for pos in portfolio.values()
                        )
                        equity = cash + portfolio_value

                        timestamps.append(date)
                        realized_pnl_history.append(realized_pnl)
                        unrealized_pnl_history.append(unrealized_pnl)
                        equity_history.append(equity)

                        # 🖨️ Статистика
                        print(f"💰 Кэш: {cash:.2f} USDT")
                        print(f"📈 Активы (Equity): {equity:.2f} USDT")
                        print(f"📦 Портфель: {portfolio}")
                        print(f"📉 Нереализованный PnL: {unrealized_pnl:.2f} USDT")
                        print(f"💵 Реализованный PnL: {realized_pnl:.2f} USDT")

                    except Exception as e:
                        logging.error(f"Ошибка в свече: {e}")

            logging.info(f"Эмуляция завершена. Итоговый баланс: {cash:.2f} USDT")

            cash, equity, portfolio, unrealized, realized = await calculate_balance_from_orders(db, current_prices)
            print(f"✅ Финальный отчёт:")
            print(f"💰 Кэш: {cash:.2f} USDT")
            print(f"📈 Активы (Equity): {equity:.2f} USDT")
            print(f"📦 Портфель: {portfolio}")
            print(f"📉 Нереализованный PnL: {unrealized:.2f} USDT")
            print(f"💵 Реализованный PnL: {realized:.2f} USDT")

    except Exception as e:
        logging.critical(f"Ошибка в emulate_prices: {e}")


    # 📊 Отображаем график
    plot_pnl_history(timestamps, realized_pnl_history, unrealized_pnl_history, equity_history)

