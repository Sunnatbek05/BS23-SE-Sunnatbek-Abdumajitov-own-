from sqlalchemy import Column, Integer, String, Date, ForeignKey
from datetime import date
from database.db import Base

# Data model representing telegram users and preferences
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    reminder_time = Column(String, default="20:00")

# Data model representing individual tasks
class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    task_text = Column(String)
    status = Column(Integer, default=0) # 0 maps to pending, 1 to completed
    planned_for = Column(Date, default=date.today)