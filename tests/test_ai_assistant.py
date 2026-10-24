"""Проверки безопасного разбора решений AI без сетевых запросов."""

import os
import unittest

os.environ.setdefault("BOT_TOKEN", "123456:TEST_TOKEN")

from tg_LogicPulse_bot.services.ai_assistant import (  # noqa: E402
    AiAssistantError,
    AI_MAX_CONTEXT_MESSAGES,
    AI_MAX_TOKENS,
    AI_MODEL,
    AI_TEMPERATURE,
    build_completion_payload,
    validate_decision,
)


class ValidateDecisionTests(unittest.TestCase):
    def test_cloudru_generation_settings(self):
        self.assertEqual(AI_MODEL, "deepseek-ai/DeepSeek-V4-Pro")
        self.assertEqual(AI_TEMPERATURE, 0.8)
        self.assertEqual(AI_MAX_TOKENS, 1000)
        self.assertEqual(AI_MAX_CONTEXT_MESSAGES, 20)

    def test_cloudru_request_payload(self):
        payload = build_completion_payload("system", "user")
        self.assertEqual(payload["model"], "deepseek-ai/DeepSeek-V4-Pro")
        self.assertEqual(payload["temperature"], 0.8)
        self.assertEqual(payload["max_tokens"], 1000)
        self.assertEqual(payload["messages"][1]["content"], "user")

    def test_create_personal(self):
        decision = validate_decision(
            {
                "reply": "Подготовил задачу.",
                "action": {
                    "type": "create_personal",
                    "title": "Позвонить клиенту",
                    "city": "Москва",
                    "date": "20.10.2026",
                    "time": "15:30",
                },
            }
        )
        self.assertEqual(decision.action["type"], "create_personal")
        self.assertEqual(decision.action["city"], "Москва")

    def test_create_team(self):
        decision = validate_decision(
            {
                "reply": "Готово.",
                "action": {
                    "type": "create_team",
                    "text": "Подготовить отчёт для клиента",
                },
            }
        )
        self.assertEqual(decision.action["type"], "create_team")

    def test_invalid_action_is_rejected(self):
        with self.assertRaises(AiAssistantError):
            validate_decision(
                {"reply": "Удаляю всё.", "action": {"type": "delete_all"}}
            )

    def test_invalid_date_is_rejected(self):
        with self.assertRaises(AiAssistantError):
            validate_decision(
                {
                    "reply": "Готово.",
                    "action": {
                        "type": "create_personal",
                        "title": "Позвонить клиенту",
                        "city": "Москва",
                        "date": "завтра",
                        "time": "днём",
                    },
                }
            )


if __name__ == "__main__":
    unittest.main()
