from aiogram import Router, types
from aiogram.filters import Command
from database.queries import add_user
from bot.keyboards import get_main_kb

router = Router()

# Register new users and display onboarding guide
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await add_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    welcome_text = (
        f"Hello, {message.from_user.first_name}! 👋\n"
        f"I am your smart Daily Planner.\n\n"
        f"📌 <b>How to get started:</b>\n\n"
        f"1️⃣ Tap /remind — set a time for daily reminders.\n"
        f"2️⃣ Tap /plan — add tasks for Today or Tomorrow.\n"
        f"3️⃣ Tap /tasks — view checklists, mark tasks ✅, edit ✏️ or delete 🗑 them.\n\n"
        f"At the end of the week, tap /stats and /tips to get a report and AI advice 🤖!"
    )
    await message.answer(welcome_text, reply_markup=get_main_kb(), parse_mode="HTML")

# Display a quick reference of available bot commands
@router.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "📌 <b>Available Commands:</b>\n"
        "/plan - Plan tasks\n"
        "/tasks - View and manage checklists\n"
        "/history - View past days\n"
        "/stats - Productivity chart\n"
        "/tips - Smart AI advice\n"
        "/remind - Set up reminders\n"
        "/support - FAQ and Admin contact\n"
        "/help - Show this message\n"
    )
    await message.answer(help_text, parse_mode="HTML")

# Handle support and FAQ request
@router.message(Command("support"))
async def cmd_support(message: types.Message):
    support_text = (
        "❓ <b>FAQ & Support</b>\n\n"
        "<b>Q: How do I edit or delete a task?</b>\n"
        "A: Tap /tasks, select a day, and use the '⚙️ Edit / Delete' button.\n\n"
        "<b>Q: When do I get notifications?</b>\n"
        "A: Morning briefing arrives at 07:00. Evening reminder is configured via /remind.\n\n"
        "👨‍💻 <b>Need more help?</b>\n"
        "Contact the admin: @snbek"
    )
    await message.answer(support_text, parse_mode="HTML")