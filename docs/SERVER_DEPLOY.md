# LogicPulse Bot — запуск на Ubuntu

Архив содержит одного Telegram-бота. Личные задачи и командное пространство
работают через единый токен и единый процесс.

## 1. Распаковка

Распакуйте архив так, чтобы папки `LogicPulse_Bot` и `TgLP3` оставались рядом.

## 2. Проверка старых экземпляров

```bash
bash LogicPulse_Bot/deploy/check-server.sh
```

Если вывод показывает старый сервис с тем же токеном, сначала остановите именно
этот сервис. Не завершайте все процессы Python общей командой.

## 3. Первая установка

```bash
bash LogicPulse_Bot/deploy/install-server.sh
nano /opt/logicpulse-bot/LogicPulse_Bot/.env
```

Укажите токен основного бота:

```dotenv
BOT_TOKEN=ваш_токен
LEGACY_TEAM_DB_PATH=/opt/logicpulse-bot/TgLP3/tasks.db
OPENAI_API_KEY=ваш_ключ_Cloud_ru
OPENAI_BASE_URL=https://foundation-models.api.cloud.ru/v1
OPENAI_MODEL=deepseek-ai/DeepSeek-V4-Pro
TEMPERATURE=0.8
MAX_TOKENS=1000
MAX_CONTEXT_MESSAGES=20
REQUEST_TIMEOUT_SECONDS=120
LOG_LEVEL=INFO
APP_TIMEZONE=Europe/Moscow
```

Не публикуйте `.env` и не отправляйте токен в чат.

Повторите установку:

```bash
bash LogicPulse_Bot/deploy/install-server.sh
```

## 4. Проверка

```bash
systemctl is-enabled logicpulse-bot.service
systemctl is-active logicpulse-bot.service
journalctl -u logicpulse-bot.service -n 100 --no-pager
bash /opt/logicpulse-bot/LogicPulse_Bot/deploy/check-mvp-ai.sh
```

В Telegram отправьте `/start`, откройте «Командное пространство» и проверьте
активные задачи. Импорт из `TgLP3/tasks.db` идемпотентен: повторный запуск не
создаёт дубликаты.

Затем откройте «🧠 AI-помощник» и попросите создать тестовую командную задачу.
Перед записью бот обязательно покажет действие для подтверждения.
