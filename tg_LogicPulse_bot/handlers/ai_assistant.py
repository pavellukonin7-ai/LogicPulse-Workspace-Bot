"""Диалоговый AI-помощник для личных и командных задач."""

from __future__ import annotations

from datetime import datetime
from html import escape
from typing import Any

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from tg_LogicPulse_bot.database.database import db
from tg_LogicPulse_bot.keyboards import (
    get_ai_back_button,
    get_ai_confirmation,
    get_main_menu,
)
from tg_LogicPulse_bot.services.ai_assistant import AiAssistantError, ai_assistant

router = Router()


class AiAssistantStates(StatesGroup):
    waiting_for_request = State()
    waiting_for_confirmation = State()


def _command_argument(message: Message) -> str:
    parts = (message.text or "").split(maxsplit=1)
    return parts[1].strip() if len(parts) == 2 else ""


def _action_preview(action: dict[str, Any]) -> str:
    action_type = action["type"]
    if action_type == "create_personal":
        return (
            "<b>Создать личную задачу</b>\n"
            f"{escape(action['title'])}\n"
            f"⌖ {escape(action['city'])}\n"
            f"◇ {action['date']}  ·  ◷ {action['time']}"
        )
    if action_type == "create_team":
        return "<b>Создать командную задачу</b>\n" + escape(action["text"])
    if action_type == "complete_personal":
        return f"<b>Завершить личную задачу #{action['task_id']}</b>"
    if action_type == "complete_team":
        return f"<b>Завершить командную задачу #{action['task_id']}</b>"
    return ""


async def _open_assistant(target: Message | CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    if not ai_assistant.is_configured:
        text = (
            "🧠 <b>AI-помощник</b>\n\n"
            "Модуль установлен, но API-ключ пока не добавлен. "
            "Администратору нужно заполнить <code>OPENAI_API_KEY</code> в файле <code>.env</code>."
        )
    else:
        text = (
            "🧠 <b>AI-помощник для задач</b>\n\n"
            "Напишите обычной фразой, что нужно сделать. Например:\n\n"
            "• <i>Создай личную задачу: завтра в 15:00 позвонить клиенту в Москве</i>\n"
            "• <i>Добавь команде задачу подготовить коммерческое предложение</i>\n"
            "• <i>Покажи, на чём мне сосредоточиться сегодня</i>\n"
            "• <i>Разбей подготовку презентации на шаги</i>\n\n"
            "Любое изменение задач будет выполнено только после подтверждения.\n\n"
            "<i>Для ответа активные задачи передаются настроенному AI-провайдеру.</i>"
        )
        await state.set_state(AiAssistantStates.waiting_for_request)

    if isinstance(target, CallbackQuery):
        await target.message.edit_text(
            text,
            reply_markup=get_ai_back_button(),
            parse_mode="HTML",
        )
    else:
        await target.answer(text, reply_markup=get_ai_back_button(), parse_mode="HTML")


@router.callback_query(F.data == "ai_assistant")
async def ai_assistant_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await _open_assistant(callback, state)
    await callback.answer()


@router.message(Command("ai"))
async def ai_assistant_command(message: Message, state: FSMContext) -> None:
    request = _command_argument(message)
    if not request:
        await _open_assistant(message, state)
        return
    await state.clear()
    await _process_request(message, state, request)


@router.message(AiAssistantStates.waiting_for_request)
async def ai_assistant_request(message: Message, state: FSMContext) -> None:
    request = (message.text or "").strip()
    if len(request) < 3:
        await message.answer("Опишите задачу чуть подробнее.")
        return
    await _process_request(message, state, request)


async def _process_request(message: Message, state: FSMContext, request: str) -> None:
    if not ai_assistant.is_configured:
        await message.answer(
            "AI-помощник ещё не подключён. Добавьте <code>OPENAI_API_KEY</code> в <code>.env</code>.",
            parse_mode="HTML",
        )
        return
    if len(request) > 2000:
        await message.answer("Сократите запрос до 2000 символов.")
        return

    progress = await message.answer("🧠 Анализирую задачи…")
    try:
        state_data = await state.get_data()
        history = state_data.get("ai_history")
        if not isinstance(history, list):
            history = []
        personal_tasks = await db.get_user_tasks(message.from_user.id, completed=False)
        team_tasks = await db.get_team_tasks(status="open", offset=0, limit=30)
        decision = await ai_assistant.analyze(
            request=request,
            user_name=message.from_user.full_name,
            personal_tasks=personal_tasks,
            team_tasks=team_tasks,
            history=history,
        )
    except AiAssistantError as exc:
        await state.set_state(AiAssistantStates.waiting_for_request)
        await progress.edit_text(
            f"🧠 <b>AI-помощник</b>\n\n{escape(str(exc))}",
            reply_markup=get_ai_back_button(),
            parse_mode="HTML",
        )
        return

    action = decision.action
    updated_history = history + [
        {"role": "user", "content": request},
        {"role": "assistant", "content": decision.reply},
    ]
    if action["type"] == "none":
        await state.set_state(AiAssistantStates.waiting_for_request)
        await state.update_data(ai_history=updated_history)
        await progress.edit_text(
            f"🧠 <b>AI-помощник</b>\n\n{escape(decision.reply)}\n\n"
            "Можно отправить следующий запрос.",
            reply_markup=get_ai_back_button(),
            parse_mode="HTML",
        )
        return

    await state.update_data(ai_action=action, ai_history=updated_history)
    await state.set_state(AiAssistantStates.waiting_for_confirmation)
    await progress.edit_text(
        f"🧠 <b>AI подготовил действие</b>\n\n"
        f"{escape(decision.reply)}\n\n"
        f"{_action_preview(action)}\n\n"
        "Проверьте данные перед сохранением.",
        reply_markup=get_ai_confirmation(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "ai_confirm")
async def ai_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    action = data.get("ai_action")
    if not isinstance(action, dict):
        await callback.answer("Действие устарело. Повторите запрос.", show_alert=True)
        await state.clear()
        return

    action_type = action.get("type")
    result_text = "Не удалось выполнить действие."
    if action_type == "create_personal":
        datetime_obj = datetime.strptime(
            f"{action['date']} {action['time']}", "%d.%m.%Y %H:%M"
        )
        if datetime_obj <= datetime.now():
            result_text = "Указанное время уже прошло. Создайте задачу с новой датой."
        else:
            task = await db.add_task(
                user_id=callback.from_user.id,
                title=action["title"],
                city=action["city"],
                date=action["date"],
                time=action["time"],
                datetime_obj=datetime_obj,
            )
            result_text = f"✓ Личная задача #{task.id} создана."
    elif action_type == "create_team":
        task = await db.add_team_task(
            text=action["text"],
            author_name=callback.from_user.full_name,
            author_id=callback.from_user.id,
        )
        result_text = f"✓ Командная задача #{task.id} создана."
    elif action_type == "complete_personal":
        success = await db.complete_task(action["task_id"], callback.from_user.id)
        result_text = "✓ Личная задача завершена." if success else "Личная задача не найдена."
    elif action_type == "complete_team":
        success = await db.complete_team_task(action["task_id"])
        result_text = "✓ Командная задача завершена." if success else "Командная задача не найдена."

    await state.clear()
    await callback.message.edit_text(
        f"🧠 <b>AI-помощник</b>\n\n{escape(result_text)}",
        reply_markup=get_main_menu(),
        parse_mode="HTML",
    )
    await callback.answer(result_text[:180])


@router.callback_query(F.data == "ai_cancel")
async def ai_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        "Действие отменено. Данные не изменены.",
        reply_markup=get_main_menu(),
    )
    await callback.answer("Отменено")
