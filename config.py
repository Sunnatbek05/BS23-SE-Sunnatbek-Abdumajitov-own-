import os
from dotenv import load_dotenv

# Load sensitive environment variables from .env file
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Halt execution if essential Telegram token is missing
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing! Please check your .env file.")