import asyncio
import logging
import os
from datetime import datetime, timedelta
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN
from database.db import init_db
from database.queries import get_all_users_reminders, get_all_users, get_today_tasks

from bot.handlers import start, plan, settings, stats, ai_handler
from bot.keyboards import get_tasks_keyboard

# --- 1. SMART REMINDERS LOGIC ---
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

                if t_total > 0 and t_comp < t_total:
                    summary = f"📊 **Daily Progress:** {t_comp}/{t_total} tasks done.\n\n"
                    await bot.send_message(
                        user_id,
                        f"{summary}⏰ Remaining tasks for **today**:",
                        reply_markup=get_tasks_keyboard(today_tasks, today_date.isoformat()),
                        parse_mode="Markdown"
                    )
                else:
                    summary = f"🎉 **Awesome!** All tasks done!\n\n" if t_total > 0 else ""
                    tomorrow_tasks = await get_today_tasks(user_id, tomorrow_date)
                    if tomorrow_tasks:
                        await bot.send_message(
                            user_id,
                            f"{summary}⏰ Plan for **tomorrow**:",
                            reply_markup=get_tasks_keyboard(tomorrow_tasks, tomorrow_date.isoformat()),
                            parse_mode="Markdown"
                        )
                    else:
                        await bot.send_message(
                            user_id,
                            f"{summary}⏰ No tasks for tomorrow yet. Tap /plan!",
                            parse_mode="Markdown"
                        )
            except Exception as e:
                logging.error(f"Reminder error: {e}")

# --- 2. MORNING BRIEFING ---
async def send_morning_briefing(bot: Bot):
    if datetime.now().strftime("%H:%M") == "07:00":
        today = datetime.now().date()
        for user_id in await get_all_users():
            try:
                tasks = await get_today_tasks(user_id, today)
                pending = [t for t in tasks if t[2] == 0]
                if pending:
                    txt = "\n".join([f"🔹 {t[1]}" for t in pending])
                    await bot.send_message(user_id, f"Good morning! ☀️\nToday's plan:\n\n{txt}\n\nTap /tasks!")
            except: continue

# --- 3. BOT COMMANDS ---
async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="plan", description="Plan tasks"),
        BotCommand(command="tasks", description="Checklists"),
        BotCommand(command="stats", description="Productivity chart"),
        BotCommand(command="tips", description="AI Advice"),
        BotCommand(command="history", description="View history"),
        BotCommand(command="remind", description="Setup reminders"),
        BotCommand(command="help", description="Show help")
    ]
    await bot.set_my_commands(commands)

# --- 4. WEB SERVER FOR RENDER HEALTH CHECK ---
async def handle_ping(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    # Binding to 0.0.0.0 and using PORT from environment
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"🌐 Web server started on port {port}")

# --- 5. MAIN ENTRY POINT ---
async def main():
    logging.basicConfig(level=logging.INFO)
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # START WEB SERVER FOR RENDER
    await start_web_server()

    # SCHEDULER
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_reminders, "interval", minutes=1, args=(bot,))
    scheduler.add_job(send_morning_briefing, "interval", minutes=1, args=(bot,))
    scheduler.start()

    # ROUTERS
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