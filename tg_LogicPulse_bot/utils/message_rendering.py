"""Безопасная навигация между текстовыми и медиа-сообщениями Telegram."""

from __future__ import annotations

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup, Message


async def show_text_screen(
    message: Message,
    text: str,
    *,
    reply_markup: InlineKeyboardMarkup | None = None,
    parse_mode: str | None = "HTML",
):
    """Заменить текстовое сообщение или отправить новый экран после медиа."""
    if message.text is not None:
        return await message.edit_text(
            text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )

    # У документа или изображения нельзя заменить caption обычным текстом.
    # Снимаем кнопки с медиа и открываем новый текстовый экран.
    try:
        await message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass

    return await message.answer(
        text,
        reply_markup=reply_markup,
        parse_mode=parse_mode,
    )
