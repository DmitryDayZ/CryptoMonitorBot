from aiogram import Bot, Dispatcher

from tgbot.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()


async def send_price_alert(exchange, pair, old, new, diff, direction, timestamp, strategy=None):
    sign = "+" if new > old else "-"
    icon = "📈" if new > old else "📉"
    old_icon = "🔻" if new > old else "🔺"
    new_icon = "🔺" if new > old else "🔻"

    # Форматируем timestamp, если он datetime
    if hasattr(timestamp, "strftime"):
        timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")

    text = (
        f"📊 <b>Биржа:</b> <i>{exchange}</i>\n"
        f"💱 <b>Пара:</b> <i>{pair}</i>\n\n"
        f"{icon} <b>Изменение:</b> <b><u>{sign}{diff:.2f}%</u></b>\n"
        f"{old_icon} <b>Старая цена:</b> <code>{old}</code>\n"
        f"{new_icon} <b>Новая цена:</b> <code>{new}</code>\n"
        f"🕒 <b>Время:</b> <i>{timestamp}</i>\n"
        f"🧭 <b>Направление:</b> {direction}"
    )
    if strategy:
        text += f"\n📐 <b>Стратегия:</b> <i>{strategy}</i>"

    await bot.send_message(
        TELEGRAM_CHAT_ID,
        text,
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


async def send_text(message):
    try:
        await bot.send_message(TELEGRAM_CHAT_ID, message, parse_mode="HTML")
    except Exception as e:
        print(f"Ошибка при отправке сообщения в Telegram: {e}")



