import re
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.queries import get_history_dates, get_tasks_by_date, update_reminder_time
from bot.keyboards import get_history_kb, get_reminder_kb, get_history_back_kb, get_main_kb

router = Router()

class ReminderStates(StatesGroup):
    waiting_for_time = State()

# Display dates with task history
@router.message(Command("history"))
async def cmd_history(message: types.Message):
    dates = await get_history_dates(message.from_user.id)
    if not dates:
        await message.answer("History is empty. Plan something!")
        return
    await message.answer("Select a date to view the report:", reply_markup=get_history_kb(dates))

# Render task report for selected date
@router.callback_query(F.data.startswith("hist_"))
async def show_history_date(callback: types.CallbackQuery):
    date_str = callback.data.split("_")[1]
    tasks = await get_tasks_by_date(callback.from_user.id, date_str)

    history_text = f"📜 **Report for {date_str}:**\n\n"
    for text, status in tasks:
        icon = "✅" if status == 1 else "❌"
        history_text += f"{icon} {text}\n"

    await callback.message.edit_text(history_text, parse_mode="Markdown", reply_markup=get_history_back_kb())
    await callback.answer()

# Return to history dates menu
@router.callback_query(F.data == "history_back")
async def handle_history_back(callback: types.CallbackQuery):
    dates = await get_history_dates(callback.from_user.id)
    if not dates:
        await callback.message.edit_text("History is empty. Plan something!")
        return
    await callback.message.edit_text("Select a date to view the report:", reply_markup=get_history_kb(dates))
    await callback.answer()

# Trigger reminder setup
@router.message(Command("remind"))
async def cmd_remind(message: types.Message, state: FSMContext):
    await message.answer(
        "At what time should I send you a reminder?\n\n"
        "👇 Tap a quick button below,\n"
        "✍️ **OR just type your preferred time** (e.g., `08:30` or `14:15`):",
        reply_markup=get_reminder_kb(),
        parse_mode="Markdown"
    )
    await state.set_state(ReminderStates.waiting_for_time)

# Process predefined time selection
@router.callback_query(F.data.startswith("set_time_"))
async def handle_set_time(callback: types.CallbackQuery, state: FSMContext):
    new_time = callback.data.split("_")[2]
    await update_reminder_time(callback.from_user.id, new_time)

    await callback.message.delete()
    await callback.message.answer(f"🔔 Done! Reminder set for {new_time}.", reply_markup=get_main_kb())

    await state.clear()
    await callback.answer()

# Validate and save custom reminder time
@router.message(ReminderStates.waiting_for_time)
async def process_custom_time(message: types.Message, state: FSMContext):
    if message.text.startswith('/'):
        await state.clear()
        await message.answer("Action canceled.", reply_markup=get_main_kb())
        return

    custom_time = message.text.strip()

    if re.match(r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$", custom_time):
        if len(custom_time) == 4:
            custom_time = "0" + custom_time

        await update_reminder_time(message.from_user.id, custom_time)
        await message.answer(f"🔔 Done! Reminder set for {custom_time}.", reply_markup=get_main_kb())
        await state.clear()
    else:
        await message.answer("⚠️ Invalid format! Please enter time in HH:MM format (e.g., `08:30` or `21:15`).", parse_mode="Markdown")