from aiogram import Bot
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

bot = Bot(token=TELEGRAM_BOT_TOKEN)

async def send_price_alert(exchange, pair, old, new, diff, direction):
    sign = "+" if new > old else "-"

    text = (
        f"📊 <b>Биржа:</b> <i>{exchange}</i>\n"
        f"🔄 <b>Торговая пара:</b> <i>{pair}</i>\n\n"
        f"📈 <b>Изменение цены:</b> <b><u>{sign}{diff:.2f}%</u></b>\n"
        f"🔻 <b>Старая цена:</b> <code>{old}</code>\n"
        f"🔺 <b>Новая цена:</b> <code>{new}</code>\n\n"
        f"👉 <b>Направление:</b> {direction}"
    )

    await bot.send_message(TELEGRAM_CHAT_ID, text, parse_mode="HTML")

