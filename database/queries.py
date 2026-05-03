from sqlalchemy import select, func, update, delete
from datetime import datetime, date
from database.db import async_session
from database.models import User, Task

# Register a new user in the database
async def add_user(user_id: int, username: str, full_name: str):
    async with async_session() as session:
        user = await session.get(User, user_id)
        if not user:
            new_user = User(id=user_id, username=username, full_name=full_name)
            session.add(new_user)
            await session.commit()

# Insert a new task
async def save_task(user_id: int, task_text: str, planned_date: date):
    async with async_session() as session:
        new_task = Task(user_id=user_id, task_text=task_text, planned_for=planned_date)
        session.add(new_task)
        await session.commit()

# Retrieve tasks scheduled for a specific date
async def get_today_tasks(user_id: int, target_date: date):
    async with async_session() as session:
        result = await session.execute(
            select(Task.id, Task.task_text, Task.status)
            .where(Task.user_id == user_id, Task.planned_for == target_date)
        )
        return result.all()

# Switch task status between completed (1) and pending (0)
async def toggle_task_status(task_id: int):
    async with async_session() as session:
        task = await session.get(Task, task_id)
        if task:
            task.status = 1 - task.status
            task_date = task.planned_for
            await session.commit()
            return task_date
        return None

# Fetch tasks that are pending from previous days
async def get_unfinished_tasks(user_id: int, today: date):
    async with async_session() as session:
        result = await session.execute(
            select(Task.id, Task.task_text)
            .where(Task.user_id == user_id, Task.status == 0, Task.planned_for < today)
        )
        return result.all()

# Reschedule pending past tasks to a new target date
async def carry_over_tasks(user_id: int, today: date, target_date: date):
    async with async_session() as session:
        await session.execute(
            update(Task)
            .where(Task.user_id == user_id, Task.status == 0, Task.planned_for < today)
            .values(planned_for=target_date)
        )
        await session.commit()

# Delete all pending tasks for a specific date
async def clear_tasks_by_date(user_id: int, target_date: date):
    async with async_session() as session:
        await session.execute(
            delete(Task)
            .where(Task.user_id == user_id, Task.planned_for == target_date, Task.status == 0)
        )
        await session.commit()

# Delete a task by ID
async def delete_task(task_id: int):
    async with async_session() as session:
        task = await session.get(Task, task_id)
        if task:
            task_date = task.planned_for
            await session.delete(task)
            await session.commit()
            return task_date
        return None

# Update task text content
async def update_task_text(task_id: int, new_text: str):
    async with async_session() as session:
        task = await session.get(Task, task_id)
        if task:
            task.task_text = new_text
            await session.commit()

# Get a list of dates where the user had tasks
async def get_history_dates(user_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Task.planned_for)
            .where(Task.user_id == user_id)
            .distinct()
            .order_by(Task.planned_for.desc())
            .limit(10)
        )
        return [row[0] for row in result.all()]

# Get all tasks for a specific string date
async def get_tasks_by_date(user_id: int, date_str):
    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    async with async_session() as session:
        result = await session.execute(
            select(Task.task_text, Task.status)
            .where(Task.user_id == user_id, Task.planned_for == target_date)
        )
        return result.all()

# Update user's daily reminder time
async def update_reminder_time(user_id: int, new_time: str):
    async with async_session() as session:
        user = await session.get(User, user_id)
        if user:
            user.reminder_time = new_time
            await session.commit()

# Fetch reminder times for all users
async def get_all_users_reminders():
    async with async_session() as session:
        result = await session.execute(select(User.id, User.reminder_time))
        return result.all()

# Fetch all registered user IDs
async def get_all_users():
    async with async_session() as session:
        result = await session.execute(select(User.id))
        return [row[0] for row in result.all()]

# Calculate total and completed task counts for stats
async def get_user_stats(user_id: int):
    async with async_session() as session:
        total = await session.execute(select(func.count(Task.id)).where(Task.user_id == user_id))
        completed = await session.execute(select(func.count(Task.id)).where(Task.user_id == user_id, Task.status == 1))
        return total.scalar() or 0, completed.scalar() or 0

# Fetch all tasks to compute tag-based statistics
async def get_all_user_tasks(user_id: int):
    async with async_session() as session:
        result = await session.execute(select(Task.task_text, Task.status).where(Task.user_id == user_id))
        return result.all()

# Fetch recent tasks to feed context to the AI
async def get_recent_tasks_for_ai(user_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Task.task_text, Task.status)
            .where(Task.user_id == user_id)
            .order_by(Task.planned_for.desc())
            .limit(15)
        )
        return result.all()

# Fetch tasks within a specific date range for trend analysis
async def get_tasks_for_period(user_id: int, start_date: date, end_date: date):
    async with async_session() as session:
        result = await session.execute(
            select(Task.planned_for, Task.task_text, Task.status)
            .where(Task.user_id == user_id, Task.planned_for >= start_date, Task.planned_for <= end_date)
            .order_by(Task.planned_for)
        )
        return result.all()