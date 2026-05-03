from aiogram import Router, types, F
from aiogram.filters import Command
from database.queries import get_recent_tasks_for_ai
from ai.gemini import get_ai_tips

router = Router()

# Handle request for AI productivity advice
@router.message(Command("tips"))
async def cmd_ai_tips(message: types.Message):
    user_id = message.from_user.id

    # Notify user that the AI is processing the request
    wait_msg = await message.answer("⏳ Analyzing your tasks... Please wait a second 🤖")

    # Fetch recent context for the AI
    tasks = await get_recent_tasks_for_ai(user_id)

    if not tasks:
        await wait_msg.edit_text("You don't have any tasks to analyze yet. Add them via /plan!")
        return

    # Categorize tasks into completed and unfinished lists
    completed = [t[0] for t in tasks if t[1] == 1]
    unfinished = [t[0] for t in tasks if t[1] == 0]

    comp_text = ", ".join(completed) if completed else "No completed tasks"
    unf_text = ", ".join(unfinished) if unfinished else "All tasks completed!"

    # Fetch generated advice from Gemini API
    ai_response = await get_ai_tips(comp_text, unf_text)

    await wait_msg.edit_text(f"💡 **AI Productivity Tip:**\n\n{ai_response}", parse_mode="Markdown")