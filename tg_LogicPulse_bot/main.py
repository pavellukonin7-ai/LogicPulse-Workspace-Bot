"""
Точка входа в приложение бота
"""
import asyncio
import logging
from pathlib import Path

from tg_LogicPulse_bot.config.settings import get_logger_config
from tg_LogicPulse_bot.bot.bot import BotApplication

# Настройка логирования
log_config = get_logger_config()
logging.basicConfig(**log_config)
logger = logging.getLogger(__name__)


async def main():
    """Главная функция"""
    app = BotApplication()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())

