#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${1:-/opt/logicpulse-bot/LogicPulse_Bot}"
ENV_FILE="${APP_DIR}/.env"

[[ -f "${ENV_FILE}" ]] || {
    echo "Не найден ${ENV_FILE}" >&2
    exit 1
}

read -r -s -p "Вставьте API-ключ Cloud.ru: " CLOUDRU_API_KEY
echo
[[ -n "${CLOUDRU_API_KEY}" ]] || {
    echo "Ключ не может быть пустым." >&2
    exit 1
}

backup_file="${ENV_FILE}.backup-cloudru-$(date -u +%Y%m%dT%H%M%SZ)"
cp --preserve=mode,ownership,timestamps "${ENV_FILE}" "${backup_file}"

set_env_value() {
    local key="$1"
    local value="$2"
    local temp_file
    local replaced=0
    temp_file="$(mktemp "${ENV_FILE}.tmp.XXXXXX")"

    while IFS= read -r line || [[ -n "${line}" ]]; do
        if [[ "${line}" == "${key}="* ]]; then
            if [[ ${replaced} -eq 0 ]]; then
                printf '%s=%s\n' "${key}" "${value}" >> "${temp_file}"
                replaced=1
            fi
        else
            printf '%s\n' "${line}" >> "${temp_file}"
        fi
    done < "${ENV_FILE}"

    if [[ ${replaced} -eq 0 ]]; then
        printf '%s=%s\n' "${key}" "${value}" >> "${temp_file}"
    fi

    cat "${temp_file}" > "${ENV_FILE}"
    rm -f "${temp_file}"
}

set_env_value "OPENAI_API_KEY" "${CLOUDRU_API_KEY}"
set_env_value "OPENAI_BASE_URL" "https://foundation-models.api.cloud.ru/v1"
set_env_value "OPENAI_MODEL" "deepseek-ai/DeepSeek-V4-Pro"
set_env_value "TEMPERATURE" "0.8"
set_env_value "MAX_TOKENS" "1000"
set_env_value "MAX_CONTEXT_MESSAGES" "20"
set_env_value "REQUEST_TIMEOUT_SECONDS" "120"
set_env_value "LOG_LEVEL" "INFO"

unset CLOUDRU_API_KEY
chown logicpulse-bot:logicpulse-bot "${ENV_FILE}"
chmod 0600 "${ENV_FILE}"

systemctl restart logicpulse-bot.service
sleep 3

echo "Cloud.ru настроен. Резервная копия: ${backup_file}"
systemctl is-active logicpulse-bot.service
