"""Командное пространство, перенесённое из бота TgLP3."""

import csv
import io
import math
from html import escape

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from tg_LogicPulse_bot.database.database import db
from tg_LogicPulse_bot.keyboards import (
    get_back_button,
    get_team_menu,
    get_team_tasks_keyboard,
)

router = Router()
PAGE_SIZE = 8


class AddTeamTaskStates(StatesGroup):
    waiting_for_text = State()


def _format_created_at(value) -> str:
    if value is None:
        return "—"
    try:
        return value.strftime("%d.%m.%Y · %H:%M")
    except AttributeError:
        return str(value)


def _csv_safe(value) -> str:
    """Не позволить табличному редактору выполнить пользовательский текст."""
    text = str(value)
    if text.startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


async def _send_or_edit(target: Message | CallbackQuery, text: str, keyboard) -> None:
    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await target.answer(text, reply_markup=keyboard, parse_mode="HTML")


async def show_team_menu(target: Message | CallbackQuery) -> None:
    active = await db.count_team_tasks("open")
    completed = await db.count_team_tasks("done")
    text = (
        "◆ <b>Командное пространство</b>\n"
        "<i>Единый список для всей команды</i>\n\n"
        f"<b>{active}</b> активных  ·  <b>{completed}</b> завершённых\n\n"
        "Создавайте общие задачи, отмечайте результат и выгружайте реестр в CSV."
    )
    await _send_or_edit(target, text, get_team_menu())


@router.message(Command("team"))
async def team_command(message: Message) -> None:
    await show_team_menu(message)


@router.callback_query(F.data == "team_tasks")
async def team_menu_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await show_team_menu(callback)
    await callback.answer()


async def _start_team_add(target: Message | CallbackQuery, state: FSMContext) -> None:
    text = (
        "＋ <b>Новая командная задача</b>\n\n"
        "Опишите результат, который должен увидеть ваш коллега.\n"
        "Одного понятного сообщения достаточно."
    )
    await _send_or_edit(target, text, get_back_button("team_tasks"))
    await state.set_state(AddTeamTaskStates.waiting_for_text)


@router.message(Command("team_add"))
async def team_add_command(message: Message, state: FSMContext) -> None:
    await _start_team_add(message, state)


@router.callback_query(F.data == "team_add")
async def team_add_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await _start_team_add(callback, state)
    await callback.answer()


@router.message(AddTeamTaskStates.waiting_for_text)
async def save_team_task(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if len(text) < 3:
        await message.answer("Добавьте чуть больше деталей — минимум 3 символа.")
        return
    if len(text) > 800:
        await message.answer("Сократите описание до 800 символов.")
        return

    author_name = message.from_user.full_name if message.from_user else "Участник"
    author_id = message.from_user.id if message.from_user else None
    task = await db.add_team_task(text, author_name, author_id)
    await state.clear()
    await message.answer(
        "✓ <b>Командная задача создана</b>\n\n"
        f"<b>#{task.id}</b>  {escape(task.text)}\n"
        f"<i>Автор: {escape(task.author_name)}</i>",
        reply_markup=get_team_menu(),
        parse_mode="HTML",
    )


async def show_team_list(
    target: Message | CallbackQuery,
    page: int = 0,
    done: bool = False,
) -> None:
    status = "done" if done else "open"
    total = await db.count_team_tasks(status)
    total_pages = max(1, math.ceil(total / PAGE_SIZE))
    page = max(0, min(page, total_pages - 1))
    tasks = await db.get_team_tasks(
        status=status,
        offset=page * PAGE_SIZE,
        limit=PAGE_SIZE,
    )

    title = "✓ Завершённые командные" if done else "◷ Активные командные"
    if not tasks:
        text = f"<b>{title}</b>\n\nСписок пока пуст."
    else:
        blocks = [f"<b>{title}</b>", f"<i>{total} задач · страница {page + 1}</i>"]
        for task in tasks:
            blocks.append(
                f"<b>#{task.id}</b>  {escape(task.text)}\n"
                f"<i>{escape(task.author_name)}  ·  {_format_created_at(task.created_at)}</i>"
            )
        text = "\n\n".join(blocks)

    keyboard = get_team_tasks_keyboard(tasks, page, total_pages, done=done)
    await _send_or_edit(target, text, keyboard)


@router.callback_query(F.data.startswith("team_list:"))
async def team_list_callback(callback: CallbackQuery) -> None:
    page = int(callback.data.rsplit(":", 1)[1])
    await show_team_list(callback, page=page, done=False)
    await callback.answer()


@router.callback_query(F.data.startswith("team_done:"))
async def team_done_callback(callback: CallbackQuery) -> None:
    page = int(callback.data.rsplit(":", 1)[1])
    await show_team_list(callback, page=page, done=True)
    await callback.answer()


@router.callback_query(F.data.startswith("team_complete:"))
async def team_complete_callback(callback: CallbackQuery) -> None:
    _, task_id, page = callback.data.split(":")
    success = await db.complete_team_task(int(task_id))
    await callback.answer(
        "Задача завершена" if success else "Задача уже недоступна",
        show_alert=not success,
    )
    await show_team_list(callback, page=int(page), done=False)


@router.callback_query(F.data.startswith("team_delete:"))
async def team_delete_callback(callback: CallbackQuery) -> None:
    _, task_id, page, source = callback.data.split(":")
    success = await db.delete_team_task(int(task_id))
    await callback.answer(
        "Задача удалена" if success else "Задача уже недоступна",
        show_alert=not success,
    )
    await show_team_list(callback, page=int(page), done=source == "done")


@router.callback_query(F.data == "team_noop")
async def team_noop(callback: CallbackQuery) -> None:
    await callback.answer()


async def export_team_csv(message: Message) -> None:
    tasks = await db.get_team_tasks(status=None, offset=0, limit=10000)
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["id", "task", "author", "created_at", "status"])
    for task in tasks:
        writer.writerow(
            [
                task.id,
                _csv_safe(task.text),
                _csv_safe(task.author_name),
                _format_created_at(task.created_at),
                task.status,
            ]
        )
    payload = "\ufeff" + output.getvalue()
    document = BufferedInputFile(payload.encode("utf-8"), filename="logicpulse_team.csv")
    await message.answer_document(
        document,
        caption="◆ Экспорт командного пространства LogicPulse",
    )


@router.message(Command("team_csv"))
async def team_csv_command(message: Message) -> None:
    await export_team_csv(message)


def _command_argument(message: Message) -> str:
    text = message.text or ""
    parts = text.split(maxsplit=1)
    return parts[1].strip() if len(parts) == 2 else ""


@router.message(Command("team_done"))
async def team_done_command(message: Message) -> None:
    """Совместимая командная отметка задачи по ID."""
    argument = _command_argument(message)
    if not argument.isdigit():
        await message.answer("Использование: <code>/team_done ID</code>", parse_mode="HTML")
        return
    success = await db.complete_team_task(int(argument))
    await message.answer("✓ Задача завершена." if success else "Задача не найдена.")


@router.message(Command("team_delete"))
async def team_delete_command(message: Message) -> None:
    """Совместимое удаление командной задачи по ID."""
    argument = _command_argument(message)
    if not argument.isdigit():
        await message.answer(
            "Использование: <code>/team_delete ID</code>", parse_mode="HTML"
        )
        return
    success = await db.delete_team_task(int(argument))
    await message.answer("Задача удалена." if success else "Задача не найдена.")


@router.message(Command("team_user"))
async def team_user_command(message: Message) -> None:
    """Сохранённый из TgLP3 фильтр общих задач по автору."""
    author_name = _command_argument(message)
    if not author_name:
        await message.answer(
            "Использование: <code>/team_user Имя автора</code>", parse_mode="HTML"
        )
        return
    tasks = await db.get_team_tasks_by_author(author_name)
    if not tasks:
        await message.answer("Задачи этого автора не найдены.")
        return
    blocks = [f"◆ <b>Задачи автора: {escape(author_name)}</b>"]
    for task in tasks:
        status = "✓" if task.status == "done" else "◷"
        blocks.append(f"{status} <b>#{task.id}</b>  {escape(task.text)}")
    await message.answer("\n\n".join(blocks), parse_mode="HTML")


@router.callback_query(F.data == "team_export")
async def team_export_callback(callback: CallbackQuery) -> None:
    await export_team_csv(callback.message)
    await callback.answer("CSV подготовлен")
