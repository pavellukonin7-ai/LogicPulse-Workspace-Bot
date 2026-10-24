"""Единая точка запуска основного бота LogicPulse."""

import asyncio

from tg_LogicPulse_bot.main import main


if __name__ == "__main__":
    asyncio.run(main())

