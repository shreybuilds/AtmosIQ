from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN =os.getenv("BOT_TOKEN")
GROQ_API_KEY =os.getenv("GROQ_API_KEY")
DB_URL =os.getenv("DB_URL")
ALERT_DEFAULT_TIME ="06:00"
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "8296885092"))

