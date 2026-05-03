from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# Build main reply keyboard layout
def get_main_kb():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="/plan"), KeyboardButton(text="/tasks")],[KeyboardButton(text="/stats"), KeyboardButton(text="/tips")],
            [KeyboardButton(text="/history"), KeyboardButton(text="/remind")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Choose an action..."
    )
    return keyboard

# Inline keyboard to select date context for viewing checklists
def get_view_date_kb():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="📅 Today", callback_data="view_today"))
    builder.add(InlineKeyboardButton(text="🌅 Tomorrow", callback_data="view_tomorrow"))
    builder.adjust(2)
    return builder.as_markup()

# Inline keyboard to select target date for new tasks
def get_plan_date_kb():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="📅 Today", callback_data="plan_today"))
    builder.add(InlineKeyboardButton(text="🌅 Tomorrow", callback_data="plan_tomorrow"))
    builder.adjust(2)
    return builder.as_markup()

# Build interactive checklist with status toggles
def get_tasks_keyboard(tasks, date_str):
    builder = InlineKeyboardBuilder()
    for task_id, text, status in tasks:
        icon = "✅" if status == 1 else "❌"
        builder.row(InlineKeyboardButton(text=f"{icon} {text}", callback_data=f"toggle_{task_id}"))

    if tasks:
        builder.row(
            InlineKeyboardButton(text="⚙️ Edit / Delete", callback_data=f"manage_{date_str}"),
            InlineKeyboardButton(text="🗑 Clear All", callback_data=f"clear_{date_str}")
        )
    return builder.as_markup()

# Build management menu with edit and delete operations
def get_manage_keyboard(tasks, date_str):
    builder = InlineKeyboardBuilder()
    for task_id, text, status in tasks:
        builder.row(
            InlineKeyboardButton(text=f"✏️ {text}", callback_data=f"edit_{task_id}"),
            InlineKeyboardButton(text="🗑", callback_data=f"del_{task_id}")
        )
    builder.row(InlineKeyboardButton(text="🔙 Back to Checklist", callback_data=f"back_{date_str}"))
    return builder.as_markup()

# Render pagination buttons for task history view
def get_history_kb(dates):
    builder = InlineKeyboardBuilder()
    for date in dates:
        builder.add(InlineKeyboardButton(text=str(date), callback_data=f"hist_{date}"))
    builder.adjust(2)
    return builder.as_markup()

# Render predefined time options for reminder configuration
def get_reminder_kb():
    builder = InlineKeyboardBuilder()
    times =["18:00", "19:00", "20:00", "21:00", "22:00", "23:00"]
    for t in times:
        builder.add(InlineKeyboardButton(text=t, callback_data=f"set_time_{t}"))
    builder.adjust(3)
    return builder.as_markup()

# Navigation button to return to the history dates list
def get_history_back_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 Back to dates", callback_data="history_back"))
    return builder.as_markup()

# Inline keyboard to select statistics period
def get_stats_kb():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="📅 Week", callback_data="stats_week"))
    builder.add(InlineKeyboardButton(text="📆 Month", callback_data="stats_month"))
    builder.add(InlineKeyboardButton(text="📊 All Time", callback_data="stats_all"))
    builder.adjust(3)
    return builder.as_markup()