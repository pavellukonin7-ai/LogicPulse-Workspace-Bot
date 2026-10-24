"""
Обработчики работы с задачами
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from datetime import datetime
from html import escape

from tg_LogicPulse_bot.database.database import db
from tg_LogicPulse_bot.keyboards import get_back_button, get_personal_tasks_keyboard

router = Router()


def format_task(task) -> str:
    """Форматирование задачи для отображения"""
    status = "✅ Выполнена" if task.is_completed else "⏰ Запланирована"
    
    text = (
        f"📝 <b>{escape(task.title)}</b>\n"
        f"🏙 <b>Город:</b> {escape(task.city)}\n"
        f"📅 <b>Дата:</b> {task.date}\n"
        f"⏰ <b>Время:</b> {task.time}\n"
        f"📊 <b>Статус:</b> {status}\n"
    )
    return text


async def show_my_tasks(message: Message | CallbackQuery):
    """Показать все запланированные задачи пользователя"""
    if isinstance(message, Message):
        user_id = message.from_user.id
    else:
        user_id = message.from_user.id
    
    # Показываем только запланированные (невыполненные) задачи
    tasks = await db.get_user_tasks(int(user_id), completed=False)
    
    if not tasks:
        text = (
            "◷ <b>Мои планы</b>\n\n"
            "Здесь пока спокойно. Создайте первую личную задачу."
        )
        keyboard = get_back_button("main_menu")
    else:
        text = "◷ <b>Мои планы</b>\n<i>Активные личные задачи</i>\n\n"
        visible_tasks = tasks[:8]
        for i, task in enumerate(visible_tasks, 1):
            # Определяем, прошла ли дата задачи
            now = datetime.now()
            if task.datetime_obj < now:
                time_status = "⏳ Прошло"
            else:
                time_status = "⏰ Предстоит"
            
            text += (
                f"<b>{i:02}. {escape(task.title)}</b>\n"
                f"⌖ {escape(task.city)}  ·  ◇ {task.date}  ·  ◷ {task.time}\n"
                f"{time_status}\n\n"
            )
        if len(tasks) > len(visible_tasks):
            text += f"<i>И ещё {len(tasks) - len(visible_tasks)} задач.</i>\n"
        keyboard = get_personal_tasks_keyboard(visible_tasks)
    
    if isinstance(message, CallbackQuery):
        await message.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


async def show_scheduled_tasks(message: Message | CallbackQuery):
    """Показать все запланированные задачи пользователя"""
    if isinstance(message, Message):
        user_id = message.from_user.id
    else:
        user_id = message.from_user.id
    
    # Получаем все невыполненные задачи пользователя
    tasks = await db.get_user_tasks(int(user_id), completed=False)
    
    if not tasks:
        text = (
            "◷ <b>Мои планы</b>\n\n"
            "Здесь пока спокойно. Создайте первую личную задачу."
        )
        keyboard = get_back_button("main_menu")
    else:
        text = "◷ <b>Мои планы</b>\n<i>Активные личные задачи</i>\n\n"
        visible_tasks = tasks[:8]
        for i, task in enumerate(visible_tasks, 1):
            # Определяем, прошла ли дата задачи
            now = datetime.now()
            if task.datetime_obj < now:
                time_status = "⏳ Прошло"
            else:
                time_status = "⏰ Предстоит"
            
            text += (
                f"<b>{i:02}. {escape(task.title)}</b>\n"
                f"⌖ {escape(task.city)}  ·  ◇ {task.date}  ·  ◷ {task.time}\n"
                f"{time_status}\n\n"
            )
        if len(tasks) > len(visible_tasks):
            text += f"<i>И ещё {len(tasks) - len(visible_tasks)} задач.</i>\n"
        keyboard = get_personal_tasks_keyboard(visible_tasks)
    
    if isinstance(message, CallbackQuery):
        await message.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


async def show_completed_tasks(message: Message | CallbackQuery):
    """Показать завершённые личные задачи."""
    user_id = message.from_user.id
    tasks = await db.get_user_tasks(int(user_id), completed=True)
    if not tasks:
        text = "✓ <b>Завершённые</b>\n\nИстория пока пуста."
    else:
        lines = ["✓ <b>Завершённые</b>", "<i>Личная история</i>", ""]
        for index, task in enumerate(tasks[:20], 1):
            lines.append(
                f"<b>{index:02}. {escape(task.title)}</b>\n"
                f"⌖ {escape(task.city)}  ·  ◇ {task.date}  ·  ◷ {task.time}"
            )
        text = "\n\n".join(lines)
    keyboard = get_back_button("main_menu")
    
    if isinstance(message, CallbackQuery):
        await message.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("complete_task_"))
async def complete_task(callback: CallbackQuery):
    """Отметить личную задачу выполненной и сохранить в истории."""
    task_id = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id
    
    # Получаем информацию о задаче перед изменением статуса
    task = await db.get_task_by_id(task_id, user_id)
    
    if task:
        success = await db.complete_task(task_id, user_id)
        
        if success:
            await callback.answer(
                f"✓ Задача «{task.title[:80]}» завершена",
                show_alert=True
            )
            # Показываем обновленный список запланированных задач
            await show_scheduled_tasks(callback)
        else:
            await callback.answer("Не удалось завершить задачу", show_alert=True)
    else:
        await callback.answer("❌ Задача не найдена!", show_alert=True)


@router.callback_query(F.data.startswith("delete_task_"))
async def delete_task(callback: CallbackQuery):
    """Удалить задачу из запланированных"""
    task_id = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id
    
    # Получаем информацию о задаче перед удалением
    task = await db.get_task_by_id(task_id, user_id)
    
    if task:
        success = await db.delete_task(task_id, user_id)
        
        if success:
            await callback.answer(
                f"Задача «{task.title[:80]}» удалена",
                show_alert=True
            )
            # Показываем обновленный список запланированных задач
            await show_scheduled_tasks(callback)
        else:
            await callback.answer("❌ Ошибка при удалении задачи!", show_alert=True)
    else:
        await callback.answer("❌ Задача не найдена!", show_alert=True)
