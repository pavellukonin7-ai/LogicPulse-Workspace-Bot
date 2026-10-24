"""
Настройки бота
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv


def _env_int(name: str, default: int, minimum: int = 1) -> int:
    """Прочитать целое значение без риска остановить бот из-за опечатки."""
    try:
        return max(minimum, int(os.getenv(name, str(default))))
    except ValueError:
        return default


def _env_float(
    name: str,
    default: float,
    minimum: float = 0.0,
    maximum: float = 2.0,
) -> float:
    """Прочитать ограниченное вещественное значение из окружения."""
    try:
        return min(maximum, max(minimum, float(os.getenv(name, str(default)))))
    except ValueError:
        return default

# Загружаем переменные окружения
load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения!")

# AI-помощник является необязательным модулем. Без ключа бот продолжает
# работать как обычный MVP для личных и командных задач.
AI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("AI_API_KEY")
AI_BASE_URL = (
    os.getenv("OPENAI_BASE_URL")
    or os.getenv("AI_BASE_URL")
    or "https://foundation-models.api.cloud.ru/v1"
).rstrip("/")
AI_MODEL = (
    os.getenv("OPENAI_MODEL")
    or os.getenv("AI_MODEL")
    or "deepseek-ai/DeepSeek-V4-Pro"
)
AI_TEMPERATURE = _env_float("TEMPERATURE", 0.8)
AI_MAX_TOKENS = _env_int("MAX_TOKENS", 1000, minimum=64)
AI_MAX_CONTEXT_MESSAGES = _env_int("MAX_CONTEXT_MESSAGES", 20, minimum=1)
AI_TIMEOUT_SECONDS = _env_int(
    "REQUEST_TIMEOUT_SECONDS",
    _env_int("AI_TIMEOUT_SECONDS", 120, minimum=5),
    minimum=5,
)
AI_ENABLED = bool(AI_API_KEY)
APP_TIMEZONE = os.getenv("APP_TIMEZONE", "Europe/Moscow")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Путь к корневой директории проекта
BASE_DIR = Path(__file__).parent.parent.parent

# Путь к директории логов
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Путь к базе данных
DB_PATH = BASE_DIR / "tasks.db"

# Старая база командного бота. При первом запуске её задачи будут
# безопасно скопированы в отдельную таблицу основной базы LogicPulse.
LEGACY_TEAM_DB_PATH = Path(
    os.getenv("LEGACY_TEAM_DB_PATH", BASE_DIR.parent / "TgLP3" / "tasks.db")
)


def get_logger_config():
    """Конфигурация логирования"""
    import logging
    
    return {
        'level': getattr(logging, LOG_LEVEL, logging.INFO),
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'handlers': [
            logging.FileHandler(LOG_DIR / "bot.log", encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    }

