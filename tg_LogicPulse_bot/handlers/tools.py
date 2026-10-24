"""Бесплатные локальные инструменты: QR-коды и калькулятор."""

from __future__ import annotations

from html import escape

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from tg_LogicPulse_bot.keyboards import get_tools_back_button, get_tools_menu
from tg_LogicPulse_bot.services.calculator import CalculatorError, calculate, format_result
from tg_LogicPulse_bot.services.qr_generator import QrCodeError, generate_qr_png
from tg_LogicPulse_bot.utils.message_rendering import show_text_screen

router = Router()


class ToolStates(StatesGroup):
    waiting_for_qr = State()
    waiting_for_calculation = State()


def _command_argument(message: Message) -> str:
    parts = (message.text or "").split(maxsplit=1)
    return parts[1].strip() if len(parts) == 2 else ""


async def _show_tools(target: Message | CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    text = (
        "▦ <b>Инструменты</b>\n\n"
        "Работают прямо на сервере, без AI-запросов и дополнительной оплаты.\n\n"
        "<b>QR-код</b> — ссылка, текст, телефон, Wi-Fi или контакт.\n"
        "<b>Калькулятор</b> — скобки, степени, проценты, корни, логарифмы, "
        "тригонометрия и комплексные числа."
    )
    if isinstance(target, CallbackQuery):
        await show_text_screen(
            target.message,
            text,
            reply_markup=get_tools_menu(),
            parse_mode="HTML",
        )
    else:
        await target.answer(text, reply_markup=get_tools_menu(), parse_mode="HTML")


@router.callback_query(F.data == "tools_menu")
async def tools_menu_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await _show_tools(callback, state)
    await callback.answer()


@router.callback_query(F.data == "tool_qr")
async def qr_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(ToolStates.waiting_for_qr)
    await show_text_screen(
        callback.message,
        "▦ <b>Генератор QR-кодов</b>\n\n"
        "Отправьте ссылку, текст, номер телефона или другие данные.\n"
        "QR-код будет создан в высоком качестве. Команда отмены: /cancel",
        reply_markup=get_tools_back_button(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(Command("qr"))
async def qr_command(message: Message, state: FSMContext) -> None:
    content = _command_argument(message)
    if content:
        await state.clear()
        await _send_qr(message, content)
        return
    await state.set_state(ToolStates.waiting_for_qr)
    await message.answer(
        "▦ Отправьте данные для QR-кода. Например:\n"
        "<code>https://logicpulse.ru</code>",
        reply_markup=get_tools_back_button(),
        parse_mode="HTML",
    )


@router.message(F.text.regexp(r"(?i)^\s*созда(?:ть|й)\s+qr[\s\-‑–—]*код\s*$"))
async def qr_text_command(message: Message, state: FSMContext) -> None:
    """Понятная текстовая команда вместо обязательного /qr."""
    await state.clear()
    await state.set_state(ToolStates.waiting_for_qr)
    await message.answer(
        "▦ Отправьте данные, которые нужно поместить в QR-код.",
        reply_markup=get_tools_back_button(),
    )


@router.message(ToolStates.waiting_for_qr)
async def qr_input(message: Message, state: FSMContext) -> None:
    content = message.text or ""
    if await _send_qr(message, content):
        await state.clear()


async def _send_qr(message: Message, content: str) -> bool:
    content = content.strip()
    try:
        png = generate_qr_png(content)
    except QrCodeError as exc:
        await message.answer(f"Не удалось создать QR-код: {escape(str(exc))}", parse_mode="HTML")
        return False

    preview = content if len(content) <= 160 else content[:157] + "…"
    await message.answer_document(
        BufferedInputFile(png, filename="logicpulse_qr_hd.png"),
        caption=(
            f"▦ <b>QR-код готов</b>\n\n<code>{escape(preview)}</code>\n\n"
            "<i>Высокое качество · коррекция ошибок H · PNG без сжатия</i>"
        ),
        reply_markup=get_tools_menu(),
        parse_mode="HTML",
    )
    return True


@router.callback_query(F.data == "tool_calc")
async def calculator_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(ToolStates.waiting_for_calculation)
    await show_text_screen(
        callback.message,
        "∑ <b>Калькулятор</b>\n\n"
        "Введите выражение. Примеры:\n\n"
        "• <code>(1250 * 18%) + 340</code>\n"
        "• <code>sqrt(144) + 2^10</code>\n"
        "• <code>sin(pi / 2)</code>\n"
        "• <code>log(1000, 10)</code>\n"
        "• <code>(3 + 4*i)^2</code>\n\n"
        "Команда отмены: /cancel",
        reply_markup=get_tools_back_button(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(Command("calc"))
async def calculator_command(message: Message, state: FSMContext) -> None:
    expression = _command_argument(message)
    if expression:
        await state.clear()
        await _send_calculation(message, expression)
        return
    await state.set_state(ToolStates.waiting_for_calculation)
    await message.answer(
        "∑ Отправьте выражение. Например: <code>sqrt(144) + 2^10</code>",
        reply_markup=get_tools_back_button(),
        parse_mode="HTML",
    )


@router.message(ToolStates.waiting_for_calculation)
async def calculator_input(message: Message, state: FSMContext) -> None:
    await _send_calculation(message, message.text or "")


async def _send_calculation(message: Message, expression: str) -> None:
    try:
        result = format_result(calculate(expression))
    except CalculatorError as exc:
        await message.answer(
            f"Не удалось вычислить: {escape(str(exc))}.\n"
            "Проверьте скобки и названия функций.",
            reply_markup=get_tools_back_button(),
            parse_mode="HTML",
        )
        return

    await message.answer(
        "∑ <b>Результат</b>\n\n"
        f"<code>{escape(expression.strip())}</code>\n"
        f"= <b>{escape(result)}</b>\n\n"
        "Можно отправить следующее выражение.",
        reply_markup=get_tools_menu(),
        parse_mode="HTML",
    )
