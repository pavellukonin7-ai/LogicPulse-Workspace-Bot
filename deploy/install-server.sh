#!/usr/bin/env bash
set -Eeuo pipefail

if [[ ${EUID} -ne 0 ]]; then
    echo "Запустите установщик от root: sudo bash deploy/install-server.sh" >&2
    exit 1
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"
INSTALL_ROOT="/opt/logicpulse-bot"
APP_DIR="${INSTALL_ROOT}/LogicPulse_Bot"
LEGACY_DIR="${INSTALL_ROOT}/TgLP3"
SERVICE_FILE="/etc/systemd/system/logicpulse-bot.service"

if [[ ! -f "${SOURCE_ROOT}/LogicPulse_Bot/main.py" ]]; then
    echo "Не найдена папка LogicPulse_Bot рядом с TgLP3." >&2
    exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 не установлен." >&2
    exit 1
fi

if ! id logicpulse-bot >/dev/null 2>&1; then
    useradd --system --home-dir "${INSTALL_ROOT}" --shell /usr/sbin/nologin logicpulse-bot
fi

systemctl stop logicpulse-bot.service 2>/dev/null || true
install -d -m 0750 -o logicpulse-bot -g logicpulse-bot "${APP_DIR}" "${LEGACY_DIR}"

# Обновляем код, не перезаписывая токен, рабочую БД и логи.
tar -C "${SOURCE_ROOT}/LogicPulse_Bot" \
    --exclude='.env' \
    --exclude='tasks.db' \
    --exclude='logs' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    -cf - . | tar -C "${APP_DIR}" -xf -

if [[ ! -f "${APP_DIR}/tasks.db" ]]; then
    install -m 0600 "${SOURCE_ROOT}/LogicPulse_Bot/tasks.db" "${APP_DIR}/tasks.db"
fi

if [[ -f "${SOURCE_ROOT}/TgLP3/tasks.db" && ! -f "${LEGACY_DIR}/tasks.db" ]]; then
    install -m 0600 "${SOURCE_ROOT}/TgLP3/tasks.db" "${LEGACY_DIR}/tasks.db"
fi

if [[ ! -f "${APP_DIR}/.env" ]]; then
    install -m 0600 "${SOURCE_ROOT}/LogicPulse_Bot/.env.example" "${APP_DIR}/.env"
    chown logicpulse-bot:logicpulse-bot "${APP_DIR}/.env"
    echo "Создан ${APP_DIR}/.env. Вставьте BOT_TOKEN и повторите установку." >&2
    exit 3
fi

if grep -Eq '^BOT_TOKEN=(PASTE_|<|$)' "${APP_DIR}/.env"; then
    echo "В ${APP_DIR}/.env не задан рабочий BOT_TOKEN." >&2
    exit 3
fi

if [[ ! -x "${INSTALL_ROOT}/venv/bin/python" ]]; then
    python3 -m venv "${INSTALL_ROOT}/venv"
fi
"${INSTALL_ROOT}/venv/bin/python" -m pip install \
    --disable-pip-version-check \
    -r "${APP_DIR}/requirements.txt"

install -m 0644 "${APP_DIR}/deploy/logicpulse-bot.service" "${SERVICE_FILE}"
chown -R logicpulse-bot:logicpulse-bot "${INSTALL_ROOT}"
chmod 0600 "${APP_DIR}/.env" "${APP_DIR}/tasks.db"
[[ ! -f "${LEGACY_DIR}/tasks.db" ]] || chmod 0600 "${LEGACY_DIR}/tasks.db"

systemctl daemon-reload
systemctl enable --now logicpulse-bot.service

echo
systemctl --no-pager --full status logicpulse-bot.service || true
echo
echo "Логи: journalctl -u logicpulse-bot.service -n 100 --no-pager"
echo "Проверка MVP: bash ${APP_DIR}/deploy/check-mvp-ai.sh"
