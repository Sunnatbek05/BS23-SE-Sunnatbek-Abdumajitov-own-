from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta, date
from database.queries import (
    save_task, get_today_tasks, toggle_task_status, get_unfinished_tasks,
    carry_over_tasks, clear_tasks_by_date, delete_task, update_task_text
)
from bot.keyboards import get_tasks_keyboard, get_plan_date_kb, get_manage_keyboard, get_view_date_kb, get_main_kb

router = Router()

class PlanStates(StatesGroup):
    waiting_for_tasks = State()
    waiting_for_edit_text = State()

# Handle plan command and check past unfinished tasks
@router.message(Command("plan"))
async def cmd_plan(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    today = datetime.now().date()
    unfinished = await get_unfinished_tasks(user_id, today)

    if unfinished:
        tasks_text = "\n".join([f"• {t[1]}" for t in unfinished])
        await carry_over_tasks(user_id, today, today)
        await message.answer(
            f"⚠️ You had unfinished tasks from past days:\n{tasks_text}\n\n✅ I automatically moved them to Today's checklist."
        )
    await message.answer("When do you want to plan tasks for?", reply_markup=get_plan_date_kb())

# Process selected date for new tasks
@router.callback_query(F.data.in_(["plan_today", "plan_tomorrow"]))
async def handle_plan_date(callback: types.CallbackQuery, state: FSMContext):
    target = callback.data.split("_")[1]
    today = datetime.now().date()
    target_date = today if target == "today" else today + timedelta(days=1)

    await state.update_data(target_date=target_date.isoformat())
    day_str = "Today" if target == "today" else "Tomorrow"

    await callback.message.delete()

    # Hide main keyboard to force text input focus
    await callback.message.answer(
        f"Send me your task list for **{day_str}** ({target_date}), each on a new line.",
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(PlanStates.waiting_for_tasks)

# Save tasks to database and restore main keyboard
@router.message(PlanStates.waiting_for_tasks)
async def process_tasks(message: types.Message, state: FSMContext):
    if message.text.startswith('/'):
        await state.clear()
        await message.answer("Action canceled.", reply_markup=get_main_kb())
        return

    data = await state.get_data()
    target_date_str = data.get("target_date")
    target_date = date.fromisoformat(target_date_str) if target_date_str else (datetime.now() + timedelta(days=1)).date()

    tasks = message.text.split('\n')
    count = 0
    for t in tasks:
        if t.strip():
            await save_task(message.from_user.id, t.strip(), target_date)
            count += 1

    day_str = "Today" if target_date == datetime.now().date() else "Tomorrow"

    await message.answer(f"🚀 Done! Added {count} new task(s) for {day_str}.", reply_markup=get_main_kb())
    await state.clear()

# Display task management options
@router.message(Command("tasks"))
async def cmd_tasks(message: types.Message):
    await message.answer("Which checklist do you want to view/manage?", reply_markup=get_view_date_kb())

# Show checklist for selected date
@router.callback_query(F.data.in_(["view_today", "view_tomorrow"]))
async def handle_view_date(callback: types.CallbackQuery):
    target = callback.data.split("_")[1]
    today = datetime.now().date()
    target_date = today if target == "today" else today + timedelta(days=1)
    date_str = target_date.isoformat()
    day_str = "Today" if target == "today" else "Tomorrow"

    tasks = await get_today_tasks(callback.from_user.id, target_date)
    if not tasks:
        await callback.message.edit_text(f"No tasks for {day_str}. Use /plan to create a list.")
        return

    await callback.message.edit_text(
        f"📝 Your checklist for **{day_str}** ({target_date}):",
        reply_markup=get_tasks_keyboard(tasks, date_str),
        parse_mode="Markdown"
    )

# Toggle task status
@router.callback_query(F.data.startswith("toggle_"))
async def handle_task_click(callback: types.CallbackQuery):
    task_id = int(callback.data.split("_")[1])
    task_date = await toggle_task_status(task_id)
    if task_date:
        tasks = await get_today_tasks(callback.from_user.id, task_date)
        await callback.message.edit_reply_markup(reply_markup=get_tasks_keyboard(tasks, task_date.isoformat()))
    await callback.answer()

# Switch to management mode with edit and delete options
@router.callback_query(F.data.startswith("manage_"))
async def handle_manage_mode(callback: types.CallbackQuery):
    date_str = callback.data.split("_")[1]
    target_date = date.fromisoformat(date_str)
    tasks = await get_today_tasks(callback.from_user.id, target_date)
    await callback.message.edit_text(
        "⚙️ **Management Mode**\nTap ✏️ to edit text, or 🗑 to delete:",
        reply_markup=get_manage_keyboard(tasks, date_str),
        parse_mode="Markdown"
    )
    await callback.answer()

# Return from management mode to standard checklist
@router.callback_query(F.data.startswith("back_"))
async def handle_back_to_tasks(callback: types.CallbackQuery):
    date_str = callback.data.split("_")[1]
    target_date = date.fromisoformat(date_str)
    tasks = await get_today_tasks(callback.from_user.id, target_date)
    day_str = "Today" if target_date == datetime.now().date() else "Tomorrow"
    await callback.message.edit_text(
        f"📝 Your checklist for **{day_str}** ({target_date}):",
        reply_markup=get_tasks_keyboard(tasks, date_str),
        parse_mode="Markdown"
    )
    await callback.answer()

# Delete all pending tasks for selected date
@router.callback_query(F.data.startswith("clear_"))
async def handle_clear_all(callback: types.CallbackQuery):
    date_str = callback.data.split("_")[1]
    target_date = date.fromisoformat(date_str)
    await clear_tasks_by_date(callback.from_user.id, target_date)
    day_str = "Today" if target_date == datetime.now().date() else "Tomorrow"
    await callback.message.edit_text(f"🗑 All pending tasks for {day_str} have been cleared!")
    await callback.answer("Cleared!")

# Handle single task deletion
@router.callback_query(F.data.startswith("del_"))
async def handle_delete_click(callback: types.CallbackQuery):
    task_id = int(callback.data.split("_")[1])
    task_date = await delete_task(task_id)
    if task_date:
        date_str = task_date.isoformat()
        tasks = await get_today_tasks(callback.from_user.id, task_date)
        if tasks:
            await callback.message.edit_reply_markup(reply_markup=get_manage_keyboard(tasks, date_str))
        else:
            await callback.message.edit_text("All tasks have been deleted.")
    await callback.answer("Task deleted!")

# Prompt user for new task text and hide main keyboard
@router.callback_query(F.data.startswith("edit_"))
async def handle_edit_text_click(callback: types.CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split("_")[1])
    await state.update_data(edit_task_id=task_id)

    await callback.message.answer(
        "✏️ Send me the new text for this task:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(PlanStates.waiting_for_edit_text)
    await callback.answer()

# Update task text and restore main keyboard
@router.message(PlanStates.waiting_for_edit_text)
async def process_edit_text(message: types.Message, state: FSMContext):
    if message.text.startswith('/'):
        await state.clear()
        await message.answer("Action canceled.", reply_markup=get_main_kb())
        return

    data = await state.get_data()
    await update_task_text(data.get("edit_task_id"), message.text.strip())

    await message.answer("✅ Task updated! Use /tasks to see your checklist.", reply_markup=get_main_kb())
    await state.clear()