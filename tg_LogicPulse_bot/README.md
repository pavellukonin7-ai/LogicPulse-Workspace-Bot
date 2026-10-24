# LogicPulse Bot - Модульная структура

## Структура пакетов

```
tg_LogicPulse_bot/
├── __init__.py              # Корневой пакет
├── main.py                  # Точка входа в приложение
├── config/                  # Конфигурация
│   ├── __init__.py
│   └── settings.py          # Настройки (токен, пути, логирование)
├── bot/                     # Основная логика бота
│   ├── __init__.py
│   ├── bot.py              # Класс приложения бота
│   └── scheduler.py        # Планировщик напоминаний
├── handlers/                # Обработчики команд и callback
│   ├── __init__.py
│   ├── start.py            # Команды /start, /menu
│   ├── menu.py             # Главное меню
│   ├── add_task.py         # Добавление задач
│   └── tasks.py            # Работа с задачами
├── database/                # База данных
│   ├── __init__.py
│   ├── models.py           # Модели данных (Task)
│   └── database.py         # Работа с БД (Database)
├── keyboards/               # Клавиатуры
│   ├── __init__.py
│   └── keyboards.py        # Функции клавиатур
└── utils/                   # Утилиты (опционально)
    └── __init__.py
```

## Использование

### Запуск бота

```python
from tg_LogicPulse_bot.main import main
import asyncio

asyncio.run(main())
```

Или через командную строку:

```bash
python -m tg_LogicPulse_bot.main
```

## Импорты

Все импорты используют абсолютные пути от корневого пакета `tg_LogicPulse_bot`:

```python
from tg_LogicPulse_bot.config import BOT_TOKEN
from tg_LogicPulse_bot.database import db
from tg_LogicPulse_bot.keyboards import get_main_menu
from tg_LogicPulse_bot.handlers.start import router
```

## Преимущества модульной структуры

- ✅ Четкое разделение ответственности
- ✅ Легко тестировать отдельные модули
- ✅ Удобно расширять функционал
- ✅ Переиспользование кода
- ✅ Упрощенное сопровождение

