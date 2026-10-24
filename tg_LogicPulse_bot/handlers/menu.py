"""
Обработчики главного меню
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from tg_LogicPulse_bot.keyboards import get_main_menu, get_back_button
from tg_LogicPulse_bot.handlers.tasks import show_my_tasks, show_scheduled_tasks, show_completed_tasks
from tg_LogicPulse_bot.handlers.add_task import start_add_task
from tg_LogicPulse_bot.utils.message_rendering import show_text_screen

router = Router()


@router.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery, state: FSMContext):
    """Главное меню"""
    # Очищаем состояние, если пользователь был в процессе добавления задачи
    current_state = await state.get_state()
    if current_state:
        await state.clear()
    
    await show_text_screen(
        callback.message,
        "◆ <b>LOGICPULSE</b>\n"
        "<i>Ваш центр продуктивности</i>\n\n"
        "Выберите пространство или создайте новую задачу.",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "add_task")
async def add_task_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Добавить задачу'"""
    await start_add_task(callback, state)
    await callback.answer()


@router.callback_query(F.data == "my_tasks")
async def my_tasks_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Мои задачи'"""
    await show_my_tasks(callback)
    await callback.answer()


@router.callback_query(F.data == "scheduled")
async def scheduled_tasks_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Запланированные'"""
    await show_scheduled_tasks(callback)
    await callback.answer()


@router.callback_query(F.data == "completed")
async def completed_tasks_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Выполненные'"""
    await show_completed_tasks(callback)
    await callback.answer()


@router.callback_query(F.data == "settings")
async def settings_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Настройки'"""
    text = (
        "⚙ <b>Настройки пространства</b>\n\n"
        "<b>Часовой пояс</b>  ·  Europe/Moscow\n"
        "<b>Напоминания</b>  ·  включены\n"
        "<b>Хранение</b>  ·  локальная SQLite-база\n\n"
        "Чтобы изменить системные параметры, обновите файл <code>.env</code> "
        "и перезапустите бота."
    )
    await callback.message.edit_text(
        text,
        reply_markup=get_back_button(),
        parse_mode="HTML"
    )
    await callback.answer()
