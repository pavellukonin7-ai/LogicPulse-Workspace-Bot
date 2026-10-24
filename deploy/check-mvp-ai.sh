#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${1:-/opt/logicpulse-bot/LogicPulse_Bot}"
PYTHON_BIN="${APP_DIR%/LogicPulse_Bot}/venv/bin/python"

echo "=== LogicPulse MVP + AI + Tools ==="
echo "Каталог: ${APP_DIR}"

[[ -d "${APP_DIR}" ]] || { echo "ОШИБКА: каталог не найден"; exit 1; }
[[ -f "${APP_DIR}/.env" ]] || { echo "ОШИБКА: отсутствует .env"; exit 1; }
[[ -x "${PYTHON_BIN}" ]] || { echo "ОШИБКА: виртуальное окружение не найдено"; exit 1; }

if grep -Eq '^BOT_TOKEN=.+$' "${APP_DIR}/.env"; then
    echo "BOT_TOKEN: настроен"
else
    echo "BOT_TOKEN: НЕ настроен"
    exit 1
fi

if grep -Eq '^(OPENAI_API_KEY|AI_API_KEY)=.+$' "${APP_DIR}/.env"; then
    echo "AI-помощник: настроен"
else
    echo "AI-помощник: выключен (основной MVP продолжит работать)"
fi

ai_endpoint="$(sed -n 's/^OPENAI_BASE_URL=//p' "${APP_DIR}/.env" | tail -n 1)"
[[ -n "${ai_endpoint}" ]] || ai_endpoint="$(sed -n 's/^AI_BASE_URL=//p' "${APP_DIR}/.env" | tail -n 1)"
ai_model="$(sed -n 's/^OPENAI_MODEL=//p' "${APP_DIR}/.env" | tail -n 1)"
[[ -n "${ai_model}" ]] || ai_model="$(sed -n 's/^AI_MODEL=//p' "${APP_DIR}/.env" | tail -n 1)"
echo "AI endpoint: ${ai_endpoint:-значение по умолчанию}"
echo "AI model: ${ai_model:-значение по умолчанию}"

cd "${APP_DIR}"
"${PYTHON_BIN}" -m compileall -q tg_LogicPulse_bot main.py
BOT_TOKEN="$(sed -n 's/^BOT_TOKEN=//p' .env | head -n 1)" \
    "${PYTHON_BIN}" -c 'from tg_LogicPulse_bot.bot.bot import BotApplication; BotApplication()'
"${PYTHON_BIN}" -c 'import segno; from tg_LogicPulse_bot.services.calculator import calculate; assert calculate("2^10") == 1024'

echo "Код, QR-генератор и калькулятор: OK"
systemctl is-enabled logicpulse-bot.service 2>/dev/null || true
systemctl is-active logicpulse-bot.service 2>/dev/null || true
