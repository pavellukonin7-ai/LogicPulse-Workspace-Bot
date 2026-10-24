"""
Клавиатуры для бота
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_menu() -> InlineKeyboardMarkup:
    """Главное меню LogicPulse с разделением личного и командного контекста."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="＋  Новая личная задача", callback_data="add_task")
    )
    builder.row(
        InlineKeyboardButton(text="◷  Мои планы", callback_data="scheduled"),
        InlineKeyboardButton(text="✓  Завершённые", callback_data="completed")
    )
    builder.row(
        InlineKeyboardButton(text="◆  Командное пространство", callback_data="team_tasks")
    )
    builder.row(
        InlineKeyboardButton(text="🧠  AI-помощник", callback_data="ai_assistant")
    )
    builder.row(
        InlineKeyboardButton(text="▦  Инструменты", callback_data="tools_menu")
    )
    builder.row(
        InlineKeyboardButton(text="⚙  Настройки", callback_data="settings")
    )

    return builder.as_markup()


def get_tools_menu() -> InlineKeyboardMarkup:
    """Меню бесплатных локальных инструментов."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Создать QR-код", callback_data="tool_qr")
    )
    builder.row(
        InlineKeyboardButton(text="∑  Калькулятор", callback_data="tool_calc")
    )
    builder.row(
        InlineKeyboardButton(text="‹  Главное меню", callback_data="main_menu")
    )
    return builder.as_markup()


def get_tools_back_button() -> InlineKeyboardMarkup:
    """Возврат в меню инструментов."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="‹  Инструменты", callback_data="tools_menu")
    )
    return builder.as_markup()


def get_ai_confirmation() -> InlineKeyboardMarkup:
    """Подтверждение действия, подготовленного AI-помощником."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✓  Подтвердить", callback_data="ai_confirm"),
        InlineKeyboardButton(text="×  Отмена", callback_data="ai_cancel"),
    )
    return builder.as_markup()


def get_ai_back_button() -> InlineKeyboardMarkup:
    """Возврат из диалога с AI в главное меню."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="‹  Главное меню", callback_data="main_menu")
    )
    return builder.as_markup()


def get_task_actions(task_id: int, is_completed: bool = False) -> InlineKeyboardMarkup:
    """Действия с личной задачей."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="✓  Завершить",
            callback_data=f"complete_task_{task_id}"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="×  Удалить",
            callback_data=f"delete_task_{task_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="‹  Назад",
            callback_data="scheduled"
        )
    )
    
    return builder.as_markup()


def get_back_button(callback_data: str = "main_menu") -> InlineKeyboardMarkup:
    """Кнопка назад"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="‹  Назад", callback_data=callback_data)
    )
    return builder.as_markup()


def get_personal_tasks_keyboard(tasks) -> InlineKeyboardMarkup:
    """Компактные действия для списка личных задач."""
    builder = InlineKeyboardBuilder()
    for task in tasks[:8]:
        builder.row(
            InlineKeyboardButton(
                text=f"✓  #{task.id}", callback_data=f"complete_task_{task.id}"
            ),
            InlineKeyboardButton(
                text=f"×  #{task.id}", callback_data=f"delete_task_{task.id}"
            ),
        )
    builder.row(InlineKeyboardButton(text="‹  Главное меню", callback_data="main_menu"))
    return builder.as_markup()


def get_team_menu() -> InlineKeyboardMarkup:
    """Меню общего командного пространства."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="＋  Новая командная задача", callback_data="team_add")
    )
    builder.row(
        InlineKeyboardButton(text="◷  Активные", callback_data="team_list:0"),
        InlineKeyboardButton(text="✓  Завершённые", callback_data="team_done:0"),
    )
    builder.row(
        InlineKeyboardButton(text="⇩  Экспорт CSV", callback_data="team_export")
    )
    builder.row(InlineKeyboardButton(text="‹  Главное меню", callback_data="main_menu"))
    return builder.as_markup()


def get_team_tasks_keyboard(tasks, page: int, total_pages: int, done: bool = False):
    """Действия и пагинация списка командных задач."""
    builder = InlineKeyboardBuilder()
    if not done:
        for task in tasks:
            builder.row(
                InlineKeyboardButton(
                    text=f"✓  #{task.id}",
                    callback_data=f"team_complete:{task.id}:{page}",
                ),
                InlineKeyboardButton(
                    text=f"×  #{task.id}",
                    callback_data=f"team_delete:{task.id}:{page}:open",
                ),
            )
    else:
        for task in tasks:
            builder.row(
                InlineKeyboardButton(
                    text=f"×  Удалить #{task.id}",
                    callback_data=f"team_delete:{task.id}:{page}:done",
                )
            )

    if total_pages > 1:
        navigation = []
        prefix = "team_done" if done else "team_list"
        if page > 0:
            navigation.append(
                InlineKeyboardButton(text="‹", callback_data=f"{prefix}:{page - 1}")
            )
        navigation.append(
            InlineKeyboardButton(
                text=f"{page + 1} / {total_pages}", callback_data="team_noop"
            )
        )
        if page + 1 < total_pages:
            navigation.append(
                InlineKeyboardButton(text="›", callback_data=f"{prefix}:{page + 1}")
            )
        builder.row(*navigation)

    builder.row(InlineKeyboardButton(text="‹  Команда", callback_data="team_tasks"))
    return builder.as_markup()

