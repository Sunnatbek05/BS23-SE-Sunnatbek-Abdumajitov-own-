import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN
from database.db import init_db
from database.queries import get_all_users_reminders, get_all_users, get_today_tasks

from bot.handlers import start, plan, settings, stats, ai_handler
from bot.keyboards import get_tasks_keyboard

# Send dynamic reminder checklist based on user progress (Smart Logic)
async def send_reminders(bot: Bot):
    now = datetime.now().strftime("%H:%M")
    users = await get_all_users_reminders()

    today_date = datetime.now().date()
    tomorrow_date = today_date + timedelta(days=1)

    for user_id, rem_time in users:
        if rem_time == now:
            try:
                today_tasks = await get_today_tasks(user_id, today_date)

                t_total = len(today_tasks)
                t_comp = sum(1 for t in today_tasks if t[2] == 1)

                # CASE 1: User has unfinished tasks for today
                if t_total > 0 and t_comp < t_total:
                    summary_text = f"📊 **Daily Progress:** You completed {t_comp} out of {t_total} tasks so far!\n\n"
                    await bot.send_message(
                        user_id,
                        f"{summary_text}⏰ Here are your remaining tasks for **today** ({today_date}):",
                        reply_markup=get_tasks_keyboard(today_tasks, today_date.isoformat()),
                        parse_mode="Markdown"
                    )

                # CASE 2: All tasks are done (or no tasks for today at all)
                else:
                    summary_text = ""
                    if t_total > 0 and t_comp == t_total:
                        summary_text = f"🎉 **Awesome job!** You completed all {t_total} tasks for today!\n\n"

                    tomorrow_tasks = await get_today_tasks(user_id, tomorrow_date)

                    if tomorrow_tasks:
                        await bot.send_message(
                            user_id,
                            f"{summary_text}⏰ Here is your plan for **tomorrow** ({tomorrow_date}):",
                            reply_markup=get_tasks_keyboard(tomorrow_tasks, tomorrow_date.isoformat()),
                            parse_mode="Markdown"
                        )
                    else:
                        await bot.send_message(
                            user_id,
                            f"{summary_text}⏰ You have no tasks for **tomorrow** ({tomorrow_date}) yet!\nTap /plan to create a checklist.",
                            parse_mode="Markdown"
                        )
            except Exception as e:
                logging.error(f"Reminder error for {user_id}: {e}")
                continue

# Send morning briefing with today's pending tasks
async def send_morning_briefing(bot: Bot):
    now = datetime.now().strftime("%H:%M")

    if now == "07:00":
        today = datetime.now().date()
        users = await get_all_users()

        for user_id in users:
            tasks = await get_today_tasks(user_id, today)
            pending_tasks = [t for t in tasks if t[2] == 0]

            if pending_tasks:
                tasks_text = "\n".join([f"🔹 {t[1]}" for t in pending_tasks])
                briefing_msg = (
                    "Good morning! ☀️\n"
                    "Here is your plan for today:\n\n"
                    f"{tasks_text}\n\n"
                    "Tap /tasks to open your checklist and start working!"
                )
                try:
                    await bot.send_message(user_id, briefing_msg)
                except Exception:
                    continue

# Register commands for the Telegram menu button
async def set_bot_commands(bot: Bot):
    commands =[
        BotCommand(command="plan", description="Plan new tasks"),
        BotCommand(command="tasks", description="View and manage checklists"),
        BotCommand(command="stats", description="Productivity chart"),
        BotCommand(command="tips", description="Smart AI advice"),
        BotCommand(command="history", description="View past days"),
        BotCommand(command="remind", description="Set up reminders"),
        BotCommand(command="support", description="FAQ & Admin contact"),
        BotCommand(command="help", description="Show help message")
    ]
    await bot.set_my_commands(commands)

# Application entry point
async def main():
    logging.basicConfig(level=logging.INFO)
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Initialize scheduler for automated background jobs
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_reminders, "interval", minutes=1, args=(bot,))
    scheduler.add_job(send_morning_briefing, "interval", minutes=1, args=(bot,))
    scheduler.start()

    # Register application routers
    dp.include_router(start.router)
    dp.include_router(plan.router)
    dp.include_router(settings.router)
    dp.include_router(stats.router)
    dp.include_router(ai_handler.router)

    print("🚀 Kunlik Hisobot bot is running!")
    await set_bot_commands(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())