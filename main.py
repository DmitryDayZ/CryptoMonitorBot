import asyncio
import logging
from datetime import datetime

import betterlogging as bl

from db.sqlite_module import init_db
from emulation.testing import optimize_threshold
from services.history import load_all_data_to_dataframe
from tgbot.config import COIN_NAME
from tgbot.handlers import routers_list
from services.checker import check_prices, emulate_prices, emulate_trade

from aiogram import Dispatcher


from tgbot.telegram_bot import bot, dp


def setup_logging():
    """
    Set up logging configuration for the application.

    This method initializes the logging configuration for the application.
    It sets the log level to INFO and configures a basic colorized log for
    output. The log format includes the filename, line number, log level,
    timestamp, logger name, and log message.

    Returns:
        None

    Example usage:
        setup_logging()
    """
    log_level = logging.INFO
    bl.basic_colorized_config(level=log_level)

    logging.basicConfig(
        level=logging.INFO,
        format="%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s",
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting bot")


async def main():
    setup_logging()



    await bot.delete_webhook(drop_pending_updates=True)
    await init_db()
    await emulate_trade()
    # await optimize_threshold()
    # asyncio.create_task(check_prices())
    # asyncio.create_task(emulate_prices())

    dp.include_routers(*routers_list)
    # register_global_middlewares(dp)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
