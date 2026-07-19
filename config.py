from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN =os.getenv("BOT_TOKEN")
GROQ_API_KEY =os.getenv("GROQ_API_KEY")
DB_URL =os.getenv("DB_URL")
ALERT_DEFAULT_TIME ="06:00"
ADMIN_CHAT_ID_ENV = os.getenv("ADMIN_CHAT_ID")
ADMIN_CHAT_ID = int(ADMIN_CHAT_ID_ENV) if ADMIN_CHAT_ID_ENV else None

