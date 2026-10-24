"""
Обработчики добавления задачи
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from datetime import datetime
from html import escape
import re

from tg_LogicPulse_bot.database.database import db
from tg_LogicPulse_bot.keyboards import get_back_button, get_main_menu

router = Router()


class AddTaskStates(StatesGroup):
    """Состояния для добавления задачи"""
    waiting_for_title = State()
    waiting_for_city = State()
    waiting_for_date = State()
    waiting_for_time = State()


def validate_date(date_str: str) -> bool:
    """Проверка формата даты (12.10.2025)"""
    pattern = r'^\d{2}\.\d{2}\.\d{4}$'
    if not re.match(pattern, date_str):
        return False
    
    try:
        datetime.strptime(date_str, "%d.%m.%Y")
        return True
    except ValueError:
        return False


def validate_time(time_str: str) -> bool:
    """Проверка формата времени (10:15)"""
    pattern = r'^\d{2}:\d{2}$'
    if not re.match(pattern, time_str):
        return False
    
    try:
        hour, minute = map(int, time_str.split(':'))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return True
        return False
    except ValueError:
        return False


async def start_add_task(message: Message | CallbackQuery, state: FSMContext):
    """Начать процесс добавления задачи"""
    text = (
        "＋ <b>Новая личная задача</b>\n"
        "<i>Шаг 1 из 4</i>\n\n"
        "Как назовём задачу?"
    )
    
    if isinstance(message, CallbackQuery):
        await message.message.edit_text(text, reply_markup=get_back_button(), parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=get_back_button(), parse_mode="HTML")
    
    await state.set_state(AddTaskStates.waiting_for_title)


@router.message(Command("add"))
async def add_task_command(message: Message, state: FSMContext):
    """Быстрый вход в сценарий создания личной задачи."""
    await start_add_task(message, state)


@router.message(Command("cancel"))
async def cancel_action(message: Message, state: FSMContext):
    """Отменить любой текущий сценарий ввода."""
    await state.clear()
    await message.answer(
        "Действие отменено. Вы вернулись в главное меню.",
        reply_markup=get_main_menu(),
    )


@router.message(AddTaskStates.waiting_for_title)
async def process_title(message: Message, state: FSMContext):
    """Обработка названия задачи"""
    title = (message.text or "").strip()
    
    if len(title) < 3:
        await message.answer(
            "❌ Название задачи должно содержать минимум 3 символа.\n"
            "Попробуйте снова:"
        )
        return
    if len(title) > 120:
        await message.answer("Сократите название до 120 символов.")
        return
    
    await state.update_data(title=title)
    await message.answer(
        "⌖ <b>Шаг 2 из 4</b>\n\nВ каком городе это нужно сделать?",
        parse_mode="HTML",
    )
    await state.set_state(AddTaskStates.waiting_for_city)


@router.message(AddTaskStates.waiting_for_city)
async def process_city(message: Message, state: FSMContext):
    """Обработка города"""
    city = (message.text or "").strip()
    
    if len(city) < 2:
        await message.answer(
            "❌ Название города должно содержать минимум 2 символа.\n"
            "Попробуйте снова:"
        )
        return
    if len(city) > 80:
        await message.answer("Сократите название города до 80 символов.")
        return
    
    await state.update_data(city=city)
    await message.answer(
        "◇ <b>Шаг 3 из 4</b>\n\n"
        "Введите дату в формате <b>ДД.ММ.ГГГГ</b>\n"
        "Например: <code>12.10.2026</code>",
        parse_mode="HTML"
    )
    await state.set_state(AddTaskStates.waiting_for_date)


@router.message(AddTaskStates.waiting_for_date)
async def process_date(message: Message, state: FSMContext):
    """Обработка даты"""
    date = (message.text or "").strip()
    
    if not validate_date(date):
        await message.answer(
            "❌ Неверный формат даты!\n"
            "Используйте формат <b>ДД.ММ.ГГГГ</b> (например, 12.10.2025):",
            parse_mode="HTML"
        )
        return
    
    # Проверка, что дата не в прошлом
    try:
        date_obj = datetime.strptime(date, "%d.%m.%Y")
        if date_obj.date() < datetime.now().date():
            await message.answer(
                "❌ Дата не может быть в прошлом!\n"
                "Введите дату еще раз:"
            )
            return
    except ValueError:
        await message.answer(
            "❌ Неверная дата!\n"
            "Введите дату еще раз:"
        )
        return
    
    await state.update_data(date=date)
    await message.answer(
        "◷ <b>Шаг 4 из 4</b>\n\n"
        "Введите время в формате <b>ЧЧ:ММ</b>\n"
        "Например: <code>10:15</code>",
        parse_mode="HTML"
    )
    await state.set_state(AddTaskStates.waiting_for_time)


@router.message(AddTaskStates.waiting_for_time)
async def process_time(message: Message, state: FSMContext):
    """Обработка времени и сохранение задачи"""
    time = (message.text or "").strip()
    
    if not validate_time(time):
        await message.answer(
            "❌ Неверный формат времени!\n"
            "Используйте формат <b>ЧЧ:ММ</b> (например, 10:15):",
            parse_mode="HTML"
        )
        return
    
    # Получаем данные из состояния
    data = await state.get_data()
    title = data.get("title")
    city = data.get("city")
    date = data.get("date")
    
    # Создаем объект datetime
    try:
        date_obj = datetime.strptime(date, "%d.%m.%Y")
        hour, minute = map(int, time.split(':'))
        datetime_obj = date_obj.replace(hour=hour, minute=minute)
        
        # Проверка, что время не в прошлом
        if datetime_obj < datetime.now():
            await message.answer(
                "❌ Указанное время уже прошло!\n"
                "Введите время еще раз:"
            )
            return
        
        # Сохраняем задачу в БД
        try:
            task = await db.add_task(
                user_id=message.from_user.id,
                title=title,
                city=city,
                date=date,
                time=time,
                datetime_obj=datetime_obj
            )
            
            # Проверяем, что задача действительно сохранена
            if not task or not task.id:
                raise Exception("Задача не была сохранена в базу данных")
            
            # Форматируем сообщение
            task_text = (
                "✓ <b>Задача создана</b>\n\n"
                f"<b>{escape(title)}</b>\n"
                f"⌖ {escape(city)}\n"
                f"◇ {date}  ·  ◷ {time}\n\n"
                "Напоминание уже запланировано."
            )
            
            # Отправляем сообщение с кнопкой для просмотра задач
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            
            builder = InlineKeyboardBuilder()
            builder.row(
                InlineKeyboardButton(text="◷  Открыть мои планы", callback_data="scheduled")
            )
            builder.row(
                InlineKeyboardButton(text="‹  Главное меню", callback_data="main_menu")
            )
            
            await message.answer(
                task_text,
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
            await state.clear()
            
        except Exception as save_error:
            # Логируем ошибку для отладки
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Ошибка при сохранении задачи: {save_error}", exc_info=True)
            
            await message.answer(
                f"❌ Произошла ошибка при сохранении задачи: {str(save_error)}\n"
                "Попробуйте создать задачу заново."
            )
            await state.clear()
        
    except Exception as e:
        await message.answer(
            f"❌ Произошла ошибка при сохранении задачи: {str(e)}\n"
            "Попробуйте создать задачу заново."
        )
        await state.clear()



