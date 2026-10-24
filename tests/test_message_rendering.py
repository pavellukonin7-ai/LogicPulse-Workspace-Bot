import unittest

from tg_LogicPulse_bot.utils.message_rendering import show_text_screen


class FakeMessage:
    def __init__(self, text):
        self.text = text
        self.edited_text = None
        self.reply_markup_removed = False
        self.answered_text = None

    async def edit_text(self, text, **kwargs):
        self.edited_text = text
        return "edited"

    async def edit_reply_markup(self, **kwargs):
        self.reply_markup_removed = kwargs.get("reply_markup") is None

    async def answer(self, text, **kwargs):
        self.answered_text = text
        return "answered"


class MessageRenderingTests(unittest.IsolatedAsyncioTestCase):
    async def test_text_message_is_edited(self):
        message = FakeMessage(text="Старый экран")
        result = await show_text_screen(message, "Главное меню")
        self.assertEqual(result, "edited")
        self.assertEqual(message.edited_text, "Главное меню")
        self.assertIsNone(message.answered_text)

    async def test_document_message_gets_new_text_screen(self):
        message = FakeMessage(text=None)
        result = await show_text_screen(message, "Главное меню")
        self.assertEqual(result, "answered")
        self.assertTrue(message.reply_markup_removed)
        self.assertEqual(message.answered_text, "Главное меню")


if __name__ == "__main__":
    unittest.main()
