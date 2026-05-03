import io
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime, timedelta, date
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import BufferedInputFile
from database.queries import get_tasks_for_period
from bot.keyboards import get_stats_kb

router = Router()

# Ask user for the statistics period
@router.message(Command("stats"))
async def cmd_stats(message: types.Message):
    await message.answer("📊 Choose a period for your productivity report:", reply_markup=get_stats_kb())

# Process period selection and generate charts
@router.callback_query(F.data.startswith("stats_"))
async def process_stats(callback: types.CallbackQuery):
    period = callback.data.split("_")[1]
    user_id = callback.from_user.id
    today = datetime.now().date()

    if period == "week":
        start_date = today - timedelta(days=6)
        period_str = "Last 7 Days"
    elif period == "month":
        start_date = today - timedelta(days=29)
        period_str = "Last 30 Days"
    else:
        start_date = date.min
        period_str = "All Time"

    # Fetch data for the selected period
    tasks = await get_tasks_for_period(user_id, start_date, today)

    if not tasks:
        await callback.message.edit_text(f"You don't have any tasks for {period_str}. Use /plan to add some!")
        return

    total = len(tasks)
    completed = sum(1 for t in tasks if t[2] == 1)
    not_completed = total - completed
    completion_rate = (completed / total) * 100 if total > 0 else 0

    text = (
        f"📊 **Productivity Statistics ({period_str}):**\n\n"
        f"Total tasks: {total}\n"
        f"Completed: {completed} ({completion_rate:.0f}%)\n"
        f"Remaining: {not_completed}"
    )

    # Parse hashtags (#goal)
    tag_stats = {}
    for t_date, t_text, t_status in tasks:
        tags = re.findall(r'#\w+', t_text)
        for tag in tags:
            tag = tag.lower()
            if tag not in tag_stats:
                tag_stats[tag] = {'total': 0, 'completed': 0}
            tag_stats[tag]['total'] += 1
            if t_status == 1:
                tag_stats[tag]['completed'] += 1

    if tag_stats:
        text += "\n\n🏷 **Goal Statistics (tags):**\n"
        for tag, data in tag_stats.items():
            rate = (data['completed'] / data['total']) * 100
            text += f"{tag}: {data['completed']}/{data['total']} ({rate:.0f}%)\n"

    # Generate the appropriate chart
    fig, ax = plt.subplots(figsize=(8, 5))

    if period in ["week", "month"]:
        # Bar chart for trends over time
        date_counts = {}
        curr_d = start_date
        while curr_d <= today:
            date_counts[curr_d] = 0
            curr_d += timedelta(days=1)

        for t_date, t_text, t_status in tasks:
            if t_date in date_counts and t_status == 1:
                date_counts[t_date] += 1

        dates = list(date_counts.keys())
        counts = list(date_counts.values())

        # Optimize labels for month view
        if period == "month":
            labels =[d.strftime("%d.%m") if (i % 5 == 0 or i == len(dates)-1) else "" for i, d in enumerate(dates)]
        else:
            labels =[d.strftime("%a\n%d.%m") for d in dates]

        ax.bar(dates, counts, color='#4CAF50', edgecolor='black')
        ax.set_xticks(dates)
        ax.set_xticklabels(labels, rotation=0)
        plt.title(f"Tasks Completed Trend ({period_str})")
        plt.ylabel("Completed Tasks")

        # Force integer ticks on Y axis
        ax.yaxis.get_major_locator().set_params(integer=True)
    else:
        # Pie chart for all time
        labels =['Completed', 'Remaining']
        sizes =[completed, not_completed]
        colors =['#4CAF50', '#FFC107']
        ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        plt.title("Overall Task Completion")

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)

    photo = BufferedInputFile(buf.read(), filename="stats.png")

    await callback.message.delete()
    await callback.message.answer_photo(photo=photo, caption=text, parse_mode="Markdown")
    await callback.answer()