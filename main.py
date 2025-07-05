import asyncio
from checker import check_prices
from telegram_bot import bot
from aiogram import Dispatcher

dp = Dispatcher()

@dp.message()
async def echo(msg):
    await msg.answer("✅ Бот работает. Отслеживаем биржи.")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(check_prices())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
