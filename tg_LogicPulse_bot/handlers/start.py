"""
Обработчик команды /start
"""
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from html import escape

from tg_LogicPulse_bot.keyboards import get_main_menu

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    first_name = escape(message.from_user.first_name if message.from_user else "")
    welcome_text = (
        "◆ <b>LOGICPULSE</b>\n"
        "<i>Пространство ясных задач</i>\n\n"
        f"Рады видеть вас, <b>{first_name or 'друг'}</b>.\n"
        "Личные планы, напоминания и командные задачи теперь собраны в одном месте.\n\n"
        "<b>С чего начнём?</b>"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    """Обработчик команды /menu"""
    await message.answer(
        "◆ <b>LOGICPULSE</b>\n"
        "<i>Ваш центр продуктивности</i>\n\n"
        "Выберите пространство или создайте новую задачу.",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )
