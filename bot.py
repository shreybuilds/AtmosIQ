import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import BOT_TOKEN
from database import Database
from weather import WeatherService
from engine import GeminiSummary


class WeatherBot:
    def __init__(self):
        self.db = Database()
        self.gemini = GeminiSummary()
        self.app = Application.builder().token(BOT_TOKEN).build()
        self._register_handlers()

    def _register_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("stop", self.stop))
        self.app.add_handler(CommandHandler("setlocation", self.set_location))
        self.app.add_handler(CommandHandler("settime", self.set_time))
        self.app.add_handler(CommandHandler("weather", self.get_weather_now))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        welcome_text = (
            "☀️ *Welcome to Weather Alert Bot!*\n\n"
            "To register for daily alerts, register your city using:\n"
            "`/setlocation <city_name>`\n\n"
            "Example: `/setlocation London` or `/setlocation New York`"
        )
        await update.message.reply_text(welcome_text, parse_mode="Markdown")

    async def stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        self.db.remove_user(chat_id)
        await update.message.reply_text("🧹 You have unsubscribed from daily weather notifications.")

    async def set_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        city_query = " ".join(context.args).strip()
        if not city_query:
            await update.message.reply_text("❌ Usage error. Provide a city name: `/setlocation <city_name>`")
            return

        # Resolve coordinates using geocoding service
        result = WeatherService.resolve_city(city_query)
        if not result:
            await update.message.reply_text(
                f"❌ Could not resolve coordinates for city: '{city_query}'. Please double check the spelling.")
            return

        resolved_city = result["city"]
        lat = result["latitude"]
        lon = result["longitude"]

        self.db.add_user(chat_id, resolved_city, lat, lon)
        await update.message.reply_text(
            f"📍 Location successfully registered!\n🏙️ City: *{resolved_city}* ({lat}, {lon})", parse_mode="Markdown")

    async def set_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        try:
            time_str = context.args[0]
            parts = time_str.split(":")
            if len(parts) != 2 or not (0 <= int(parts[0]) < 24) or not (0 <= int(parts[1]) < 60):
                raise ValueError

            self.db.update_alert_time(chat_id, time_str)
            await update.message.reply_text(f"⏰ Daily alert scheduled at {time_str} UTC.")
        except (IndexError, ValueError):
            await update.message.reply_text(
                "❌ Invalid format. Use 24h format: `/settime HH:MM` (e.g., `/settime 08:30`)")

    async def get_weather_now(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user = self.db.get_user(chat_id)
        if not user:
            await update.message.reply_text("❌ Register your location first using `/setlocation <city_name>`.")
            return

        await update.message.reply_chat_action(action="typing")

        weather_service = WeatherService(user["latitude"], user["longitude"])
        weather_data = weather_service.get_weather_data_formatted()

        if "error" in weather_data:
            await update.message.reply_text("❌ Failed to fetch current weather details. Try again later.")
            return

        summary = self.gemini.generate_summary(weather_data, user["city"])
        await update.message.reply_text(summary, parse_mode="Markdown")

    def run(self):
        import asyncio
        self.loop = asyncio.get_event_loop()
        self.app.run_polling()

    def send_message(self, chat_id: int, message: str):
        if not hasattr(self, "loop") or self.loop is None:
            return
        asyncio.run_coroutine_threadsafe(
            self.app.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown"),
            self.loop
        )