#!/usr/bin/env bash
set -u

echo "=== Возможные экземпляры Telegram-ботов ==="
pgrep -af 'python(3)? .*\b(main|bot)\.py\b' || true

echo
echo "=== Сервисы, похожие на ботов ==="
systemctl list-units --type=service --all --no-pager \
    | grep -Ei 'logicpulse|taskcrew|telegram|bot' || true

echo
echo "=== Новый сервис LogicPulse ==="
systemctl --no-pager --full status logicpulse-bot.service 2>/dev/null || true
