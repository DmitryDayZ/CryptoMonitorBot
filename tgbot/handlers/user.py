import asyncio
import urllib
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from db.sqlite_module import AsyncSessionLocal, DBManager
from exchanges.ccxt_client import ExchangeManager
from services.checker import emulate_prices
from tgbot.keyboards.inline import very_simple_keyboard

user_router = Router()


@user_router.message(CommandStart())
async def user_start(message: Message):

    await message.answer("✅ Делаю эмуляцию торговли.")
    await emulate_prices()

@user_router.callback_query(F.data == "orders_info")
async def create_order(query: CallbackQuery):
    ex_manager = ExchangeManager()
    total_profit = 0.0
    total_value = 0.0
    price_cache = {}  # 💾 Кеш для цен вида: {"binance:BTC/USDT": 60700.0}

    try:
        async with AsyncSessionLocal() as session:
            db = DBManager(session)
            orders = await db.get_orders()

            if not orders:
                await query.message.answer("У вас нет открытых позиций.", parse_mode="HTML", disable_web_page_preview=True,
                                           reply_markup=very_simple_keyboard())

            commission_rate = 0.001
            text_parts = []
            current_chunk = "<b>📊 Ваши последние позиции:</b>\n\n"

            for o in orders:
                key = f"{o.exchange}:{o.symbol}"
                if key in price_cache:
                    current_price = price_cache[key]
                else:
                    current_price = await ex_manager.fetch_price(o.exchange, o.symbol)
                    price_cache[key] = current_price  # 🧠 Сохраняем в кеш

                value = current_price * o.amount
                total_value += value

                if o.side == "buy" and o.price is not None:
                    profit = (current_price - o.price) * o.amount
                    commission = (o.price * o.amount + current_price * o.amount) * commission_rate
                    side_icon = "🟢 Лонг"
                elif o.side == "sell" and o.price is not None:
                    profit = (o.price - current_price) * o.amount
                    commission = (o.price * o.amount + current_price * o.amount) * commission_rate
                    side_icon = "🔴 Шорт"
                else:
                    profit = 0
                    commission = 0
                    side_icon = "⚪️"

                net_profit = profit - commission
                status_icon = "🟢" if o.status == "emulated" else "⚪️"
                date_str = o.created_at.strftime("%Y-%m-%d %H:%M") if getattr(o, "created_at", None) else "—"
                strategy = o.strategy or "—"
                order_type = o.order_type or "—"

                block = (
                    f"<b>{side_icon}</b> <code>{o.symbol}</code> на <b>{o.exchange.capitalize()}</b>\n"
                    f"<b>Стратегия:</b> <i>{strategy}</i>\n"
                    f"<b>Тип:</b> <i>{order_type}</i> | <b>Статус:</b> <i>{o.status}</i> {status_icon}\n"
                    f"<b>Кол-во:</b> <code>{o.amount}</code> @ <b>{o.price}</b>\n"
                    f"<b>Дата:</b> <i>{date_str}</i>\n"
                    f"<b>Текущая цена:</b> <code>{current_price}</code>\n"
                    f"<b>Стоимость позиции:</b> <b>{value:.4f} USDT</b>\n"
                    f"<b>Прибыль (без комиссии):</b> <b>{profit:.4f} USDT</b>\n"
                    f"<b>Комиссия:</b> <b>{commission:.4f} USDT</b>\n"
                    f"<b>Чистая прибыль:</b> <b>{net_profit:.4f} USDT</b>\n\n"
                )

                if len(current_chunk) + len(block) > 2000:
                    text_parts.append(current_chunk)
                    current_chunk = block
                else:
                    current_chunk += block

                total_profit += net_profit

            # Завершающий блок
            current_chunk += (
                f"<b>💰 Общая чистая прибыль: <u>{total_profit:.4f} USDT</u></b>\n"
                f"<b>📦 Общая стоимость позиций: <u>{total_value:.4f} USDT</u></b>"
            )
            text_parts.append(current_chunk)

            for part in text_parts:
                is_last = part == text_parts[-1]
                await query.message.answer(
                    part,
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                    reply_markup=very_simple_keyboard() if is_last else None
                )

    except Exception as e:
        await query.message.answer(f"❗️ Произошла ошибка при получении позиций: {str(e)}")

    finally:
        await ex_manager.close_all()  # ⬅️ Обязательно, чтобы не было утечек aiohttp



@user_router.message()
async def echo(msg):
    ex_manager = ExchangeManager()
    total_profit = 0.0
    total_value = 0.0
    price_cache = {}  # 💾 Кеш для цен вида: {"binance:BTC/USDT": 60700.0}

    try:
        async with AsyncSessionLocal() as session:
            db = DBManager(session)
            orders = await db.get_orders()

            if not orders:
                await msg.answer("У вас нет открытых позиций.", parse_mode="HTML",
                                           disable_web_page_preview=True,
                                           reply_markup=very_simple_keyboard())

            commission_rate = 0.001
            text_parts = []
            current_chunk = "<b>📊 Ваши последние позиции:</b>\n\n"

            for o in orders:
                key = f"{o.exchange}:{o.symbol}"
                if key in price_cache:
                    current_price = price_cache[key]
                else:
                    current_price = await ex_manager.fetch_price(o.exchange, o.symbol)
                    price_cache[key] = current_price  # 🧠 Сохраняем в кеш

                value = current_price * o.amount
                total_value += value

                if o.side == "buy" and o.price is not None:
                    profit = (current_price - o.price) * o.amount
                    commission = (o.price * o.amount + current_price * o.amount) * commission_rate
                    side_icon = "🟢 Лонг"
                elif o.side == "sell" and o.price is not None:
                    profit = (o.price - current_price) * o.amount
                    commission = (o.price * o.amount + current_price * o.amount) * commission_rate
                    side_icon = "🔴 Шорт"
                else:
                    profit = 0
                    commission = 0
                    side_icon = "⚪️"

                net_profit = profit - commission
                status_icon = "🟢" if o.status == "emulated" else "⚪️"
                date_str = o.created_at.strftime("%Y-%m-%d %H:%M") if getattr(o, "created_at", None) else "—"
                strategy = o.strategy or "—"
                order_type = o.order_type or "—"

                block = (
                    f"<b>{side_icon}</b> <code>{o.symbol}</code> на <b>{o.exchange.capitalize()}</b>\n"
                    f"<b>Стратегия:</b> <i>{strategy}</i>\n"
                    f"<b>Тип:</b> <i>{order_type}</i> | <b>Статус:</b> <i>{o.status}</i> {status_icon}\n"
                    f"<b>Кол-во:</b> <code>{o.amount}</code> @ <b>{o.price}</b>\n"
                    f"<b>Дата:</b> <i>{date_str}</i>\n"
                    f"<b>Текущая цена:</b> <code>{current_price}</code>\n"
                    f"<b>Стоимость позиции:</b> <b>{value:.4f} USDT</b>\n"
                    f"<b>Прибыль (без комиссии):</b> <b>{profit:.4f} USDT</b>\n"
                    f"<b>Комиссия:</b> <b>{commission:.4f} USDT</b>\n"
                    f"<b>Чистая прибыль:</b> <b>{net_profit:.4f} USDT</b>\n\n"
                )

                if len(current_chunk) + len(block) > 2000:
                    text_parts.append(current_chunk)
                    current_chunk = block
                else:
                    current_chunk += block

                total_profit += net_profit

            # Завершающий блок
            current_chunk += (
                f"<b>💰 Общая чистая прибыль: <u>{total_profit:.4f} USDT</u></b>\n"
                f"<b>📦 Общая стоимость позиций: <u>{total_value:.4f} USDT</u></b>"
            )
            text_parts.append(current_chunk)

            for part in text_parts:
                is_last = part == text_parts[-1]
                await msg.answer(
                    part,
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                    reply_markup=very_simple_keyboard() if is_last else None
                )

    except Exception as e:
        await msg.answer(f"❗️ Произошла ошибка при получении позиций: {str(e)}")

    finally:
        await ex_manager.close_all()  # ⬅️ Обязательно, чтобы не было утечек aiohttp







