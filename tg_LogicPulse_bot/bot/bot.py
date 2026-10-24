"""
Основной класс приложения бота
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage

from tg_LogicPulse_bot.config.settings import BOT_TOKEN
from tg_LogicPulse_bot.database.database import db
from tg_LogicPulse_bot.handlers.start import router as start_router
from tg_LogicPulse_bot.handlers.menu import router as menu_router
from tg_LogicPulse_bot.handlers.add_task import router as add_task_router
from tg_LogicPulse_bot.handlers.tasks import router as tasks_router
from tg_LogicPulse_bot.handlers.team_tasks import router as team_tasks_router
from tg_LogicPulse_bot.handlers.tools import router as tools_router
from tg_LogicPulse_bot.handlers.ai_assistant import router as ai_assistant_router
from tg_LogicPulse_bot.bot.scheduler import ReminderScheduler
from tg_LogicPulse_bot.config.settings import LEGACY_TEAM_DB_PATH

logger = logging.getLogger(__name__)


class BotApplication:
    """Приложение бота"""
    
    def __init__(self):
        self.bot = None
        self.dp = None
        self.scheduler = None
        self.max_retries = 10
        self.retry_delay = 5
    
    async def initialize(self):
        """Инициализация бота"""
        self.bot = Bot(token=BOT_TOKEN)
        self.dp = Dispatcher(storage=MemoryStorage())
        
        # Регистрация роутеров
        self.dp.include_router(start_router)
        self.dp.include_router(menu_router)
        self.dp.include_router(add_task_router)
        self.dp.include_router(tasks_router)
        self.dp.include_router(team_tasks_router)
        self.dp.include_router(tools_router)
        self.dp.include_router(ai_assistant_router)
        
        # Инициализация базы данных
        await db.init()
        logger.info("База данных инициализирована")

        imported = await db.migrate_legacy_team_tasks(LEGACY_TEAM_DB_PATH)
        if imported:
            logger.info("Импортировано командных задач из TgLP3: %s", imported)

        await self.bot.set_my_commands(
            [
                BotCommand(command="start", description="Открыть LogicPulse"),
                BotCommand(command="menu", description="Главное меню"),
                BotCommand(command="add", description="Новая личная задача"),
                BotCommand(command="team", description="Командное пространство"),
                BotCommand(command="team_add", description="Новая командная задача"),
                BotCommand(command="team_done", description="Завершить командную задачу"),
                BotCommand(command="team_delete", description="Удалить командную задачу"),
                BotCommand(command="team_user", description="Задачи участника"),
                BotCommand(command="team_csv", description="Экспорт команды в CSV"),
                BotCommand(command="ai", description="AI-помощник для задач"),
                BotCommand(command="calc", description="Сложный калькулятор"),
                BotCommand(command="cancel", description="Отменить текущее действие"),
            ]
        )
        
        # Запуск планировщика напоминаний
        self.scheduler = ReminderScheduler(self.bot)
        await self.scheduler.start()
        logger.info("Планировщик напоминаний запущен")
    
    async def run(self):
        """Запуск бота с автоматическим переподключением"""
        retry_count = 0

        try:
            # Роутеры aiogram можно подключить к Dispatcher только один раз.
            # Поэтому приложение инициализируется один раз на процесс, а при
            # временной сетевой ошибке повторно запускается только polling.
            await self.initialize()

            while retry_count < self.max_retries:
                try:
                    logger.info("Бот запущен и готов к работе")
                    await self.dp.start_polling(
                        self.bot,
                        allowed_updates=self.dp.resolve_used_update_types(),
                        close_bot_session=False,
                        drop_pending_updates=(retry_count == 0),
                    )
                    logger.info("Polling штатно остановлен")
                    break

                except KeyboardInterrupt:
                    logger.info("Получен сигнал остановки (Ctrl+C)")
                    break

                except Exception as e:
                    retry_count += 1
                    error_str = str(e)
                    if "TelegramConflictError" in error_str or "Conflict" in error_str:
                        logger.error(
                            "⚠️ ОБНАРУЖЕН КОНФЛИКТ: Запущено несколько экземпляров бота!\n"
                            "Остановите другой экземпляр с тем же токеном."
                        )
                    logger.error(
                        f"Ошибка polling (попытка {retry_count}/{self.max_retries}): {e}",
                        exc_info=True,
                    )

                    if retry_count >= self.max_retries:
                        logger.critical("Достигнуто максимальное количество попыток переподключения")
                        raise

                    delay = 10 if "Conflict" in error_str else self.retry_delay
                    logger.info("Повторная попытка polling через %s секунд...", delay)
                    await asyncio.sleep(delay)
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Очистка ресурсов"""
        if self.scheduler:
            try:
                await asyncio.wait_for(self.scheduler.stop(), timeout=5)
            except Exception as exc:
                logger.warning("Не удалось штатно остановить планировщик: %s", exc)
            finally:
                self.scheduler = None

        try:
            await asyncio.wait_for(db.close(), timeout=5)
        except Exception as exc:
            logger.warning("Не удалось штатно закрыть базу данных: %s", exc)
        
        if self.bot:
            try:
                await asyncio.wait_for(self.bot.session.close(), timeout=5)
            except Exception as exc:
                logger.warning("Не удалось штатно закрыть Telegram-сессию: %s", exc)
            finally:
                self.bot = None

        logger.info("Ресурсы приложения штатно закрыты")

