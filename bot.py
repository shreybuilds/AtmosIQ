import asyncio
import logging
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from config import BOT_TOKEN, ADMIN_CHAT_ID
from database import Database
from weather import WeatherService
from engine import GeminiSummary

# Configure logging to write to both console and a file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("atmosiq.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("AtmosIQ")


class WeatherBot:
    def __init__(self):
        self.start_time = datetime.datetime.now()
        self.db = Database()
        self.gemini = GeminiSummary()
        self.app = Application.builder().token(BOT_TOKEN).post_init(self.post_init).build()
        self._register_handlers()
        
        if ADMIN_CHAT_ID is None:
            logger.warning("⚠️ ADMIN_CHAT_ID is not configured in .env. Admin commands are disabled.")
        else:
            logger.info(f"🔑 Admin commands configured for chat ID: {ADMIN_CHAT_ID}")

    async def post_init(self, application):
        self.loop = asyncio.get_running_loop()

    def _register_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("stop", self.stop))
        self.app.add_handler(CommandHandler("setlocation", self.set_location))
        self.app.add_handler(CommandHandler("settime", self.set_time))
        self.app.add_handler(CommandHandler("weather", self.get_weather_now))
        self.app.add_handler(CommandHandler("help", self.help_command))
        
        # Hidden Admin Commands (Not in Telegram's menu)
        self.app.add_handler(CommandHandler("stats", self.admin_stats))
        self.app.add_handler(CommandHandler("users", self.admin_users))
        self.app.add_handler(CommandHandler("health", self.admin_health))
        self.app.add_handler(CommandHandler("logs", self.admin_logs))

        # Callback handler for inline keyboard buttons
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))

        # Message handler for wizard text inputs (filters out commands)
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    def _is_admin(self, chat_id: int) -> bool:
        """Helper to restrict access to admin commands using the chat_id."""
        return chat_id == ADMIN_CHAT_ID

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        logger.info(f"User {chat_id} started the bot / setup wizard.")
        
        # Initialize user state for onboarding
        self.db.set_user_state(chat_id, "WAITING_FOR_LOCATION")

        setup_text = (
            "Let's get you set up in under 30 seconds.\n\n"
            "Step 1 of 2\n\n"
            "Please send me your city or location.\n\n"
            "Examples:\n"
            "• Varanasi\n"
            "• New Delhi\n"
            "• London\n"
            "• New York"
        )
        await update.message.reply_text(setup_text)

    async def stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        self.db.remove_user(chat_id)
        self.db.clear_user_state(chat_id)
        logger.info(f"User {chat_id} unsubscribed and cleared state.")
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
        self.db.clear_user_state(chat_id)
        logger.info(f"User {chat_id} manually set location to {resolved_city}.")
        await update.message.reply_text(
            f"📍 Location successfully registered!\n🏙️ City: *{resolved_city}* ({lat}, {lon})", parse_mode="Markdown")

    async def set_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        try:
            time_str = context.args[0]
            parts = time_str.split(":")
            if len(parts) != 2 or not (0 <= int(parts[0]) < 24) or not (0 <= int(parts[1]) < 60):
                raise ValueError

            formatted_time = f"{int(parts[0]):02d}:{int(parts[1]):02d}"
            self.db.update_alert_time(chat_id, formatted_time)
            self.db.clear_user_state(chat_id)
            logger.info(f"User {chat_id} manually set alert time to {formatted_time}.")
            await update.message.reply_text(f"⏰ Daily alert scheduled at {formatted_time} IST.")
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

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = (
            "📋 *Available Commands*\n\n"
            "/start - Enable and configure daily weather alerts.\n"
            "/stop - Disable daily weather alerts.\n"
            "/weather - Get the latest weather forecast.\n"
            "/setlocation - Update your saved location.\n"
            "/settime - Change your daily alert time.\n"
            "/help - View all available commands."
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        state = self.db.get_user_state(chat_id)
        text = update.message.text.strip()

        if state == "WAITING_FOR_LOCATION":
            logger.info(f"User {chat_id} onboarding: location input '{text}'")
            await update.message.reply_chat_action(action="typing")
            
            result = WeatherService.resolve_city(text)
            if not result:
                await update.message.reply_text(
                    f"❌ Could not resolve coordinates for city: '{text}'. Please double check the spelling."
                )
                return

            resolved_city = result["city"]
            lat = result["latitude"]
            lon = result["longitude"]

            self.db.add_user(chat_id, resolved_city, lat, lon)
            self.db.set_user_state(chat_id, "WAITING_FOR_TIME_CHOICE")
            logger.info(f"User {chat_id} onboarding: resolved and saved city '{resolved_city}'")

            # Present inline options for alert time configuration
            keyboard = [
                [
                    InlineKeyboardButton("Keep 6:00 AM", callback_data="keep_default"),
                    InlineKeyboardButton("Change Alert Time", callback_data="change_time")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            step2_text = (
                "Location saved successfully!\n\n"
                "Daily weather alerts are enabled by default at 6:00 AM.\n\n"
                "Step 2 of 2\n\n"
                "Would you like to keep the default alert time?"
            )
            await update.message.reply_text(step2_text, reply_markup=reply_markup)

        elif state == "WAITING_FOR_ALERT_TIME":
            logger.info(f"User {chat_id} onboarding: time input '{text}'")
            try:
                parts = text.split(":")
                if len(parts) != 2 or not (0 <= int(parts[0]) < 24) or not (0 <= int(parts[1]) < 60):
                    raise ValueError

                formatted_time = f"{int(parts[0]):02d}:{int(parts[1]):02d}"
                self.db.update_alert_time(chat_id, formatted_time)
                self.db.clear_user_state(chat_id)
                logger.info(f"User {chat_id} onboarding complete: alert time set to {formatted_time}")

                completion_text = (
                    "Alert time updated successfully!\n\n"
                    f"Your daily weather alerts are now scheduled for {formatted_time}.\n\n"
                    "Setup complete."
                )
                await update.message.reply_text(completion_text)
            except ValueError:
                await update.message.reply_text(
                    "❌ Invalid format. Please send your preferred alert time in HH:MM format.\n\nExample:\n07:30"
                )

        elif state == "WAITING_FOR_TIME_CHOICE":
            # Direct them back to the inline buttons if they type text instead of clicking
            keyboard = [
                [
                    InlineKeyboardButton("Keep 6:00 AM", callback_data="keep_default"),
                    InlineKeyboardButton("Change Alert Time", callback_data="change_time")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "Please select an option using the buttons below:",
                reply_markup=reply_markup
            )

        else:
            # Setup is complete or user is not in onboarding. Ignore normal text to avoid spamming the user.
            pass

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        chat_id = query.message.chat.id
        data = query.data

        await query.answer()

        state = self.db.get_user_state(chat_id)
        if state != "WAITING_FOR_TIME_CHOICE":
            # Remove buttons to avoid confusion since the wizard state is no longer waiting for a decision
            await query.edit_message_reply_markup(reply_markup=None)
            return

        if data == "keep_default":
            logger.info(f"User {chat_id} onboarding callback: keeping default time (6:00 AM)")
            self.db.clear_user_state(chat_id)
            
            # Remove inline buttons from the interactive message
            await query.edit_message_reply_markup(reply_markup=None)

            completion_text = (
                "Setup complete!\n\n"
                "AtmosIQ is now monitoring the weather for your location.\n\n"
                "Your daily weather alerts will be delivered at 6:00 AM.\n\n"
                "Use /weather anytime to check the latest forecast."
            )
            await context.bot.send_message(chat_id=chat_id, text=completion_text)

        elif data == "change_time":
            logger.info(f"User {chat_id} onboarding callback: choosing to change alert time")
            self.db.set_user_state(chat_id, "WAITING_FOR_ALERT_TIME")
            
            # Remove inline buttons from the interactive message
            await query.edit_message_reply_markup(reply_markup=None)

            prompt_text = (
                "Please send your preferred alert time in HH:MM format.\n\n"
                "Example:\n"
                "07:30"
            )
            await context.bot.send_message(chat_id=chat_id, text=prompt_text)

    # Admin commands (restricted by chat_id and hidden from Telegram command menus)

    async def admin_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        if not self._is_admin(chat_id):
            logger.warning(f"Unauthorized stats access attempt by chat_id {chat_id}")
            return

        total_users = self.db.get_total_users_count()
        active_users = self.db.get_active_users_count()
        alerts_sent = self.db.get_alerts_sent_today()

        # Calculate uptime
        uptime = datetime.datetime.now() - self.start_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{days}d " if days > 0 else ""
        uptime_str += f"{hours}h {minutes}m {seconds}s"

        # Check DB connection
        try:
            with self.db.conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
            db_status = "Connected ✅ (Healthy)"
        except Exception as e:
            db_status = f"Error ❌ ({e})"

        stats_text = (
            "📊 *AtmosIQ Bot Statistics*\n\n"
            f"• *Total Registered Users:* {total_users}\n"
            f"• *Total Active Users:* {active_users}\n"
            f"• *Total Alerts Sent Today:* {alerts_sent}\n"
            f"• *Bot Uptime:* {uptime_str}\n"
            f"• *Database Status:* {db_status}"
        )
        await update.message.reply_text(stats_text, parse_mode="Markdown")

    async def admin_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        if not self._is_admin(chat_id):
            logger.warning(f"Unauthorized users access attempt by chat_id {chat_id}")
            return

        try:
            with self.db.conn.cursor() as cur:
                cur.execute("SELECT chat_id, city, latitude, longitude, alert_time, subscribed FROM users;")
                rows = cur.fetchall()
        except Exception as e:
            await update.message.reply_text(f"❌ Error fetching users: {e}")
            return

        if not rows:
            await update.message.reply_text("👤 *Registered Users:* None", parse_mode="Markdown")
            return

        users_text = "👤 *Registered Users List:*\n\n"
        for row in rows:
            u_chat_id, u_city, _, _, u_alert_time, u_subscribed = row
            status_emoji = "✅" if u_subscribed else "❌"
            time_str = str(u_alert_time)[:5]
            users_text += (
                f"• *ID:* `{u_chat_id}` | *City:* {u_city} | *Time:* {time_str} | *Sub:* {status_emoji}\n"
            )
        await update.message.reply_text(users_text, parse_mode="Markdown")

    async def admin_health(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        if not self._is_admin(chat_id):
            logger.warning(f"Unauthorized health access attempt by chat_id {chat_id}")
            return

        uptime = datetime.datetime.now() - self.start_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{days}d " if days > 0 else ""
        uptime_str += f"{hours}h {minutes}m {seconds}s"

        try:
            with self.db.conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
            db_status = "Connected ✅ (Healthy)"
        except Exception as e:
            db_status = f"Unhealthy ❌ ({e})"

        ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        now_ist = datetime.datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")

        health_text = (
            "🏥 *AtmosIQ Health Status*\n\n"
            "• *Bot Status:* Running\n"
            f"• *Database Connection:* {db_status}\n"
            f"• *Uptime:* {uptime_str}\n"
            f"• *Current Time (IST):* {now_ist}"
        )
        await update.message.reply_text(health_text, parse_mode="Markdown")

    async def admin_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        if not self._is_admin(chat_id):
            logger.warning(f"Unauthorized logs access attempt by chat_id {chat_id}")
            return

        import os
        if not os.path.exists("atmosiq.log"):
            await update.message.reply_text("📝 No log file found yet.")
            return

        try:
            with open("atmosiq.log", "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            # Fetch last 20 lines of log messages
            last_lines = lines[-20:]
            logs_content = "".join(last_lines)
            
            msg = f"📋 *Recent Logs (Last 20 lines):*\n\n```\n{logs_content}\n```"
            await update.message.reply_text(msg, parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"❌ Error reading logs: {e}")

    def run(self):
        logger.info("Starting AtmosIQ Bot Polling...")
        self.app.run_polling()

    def send_message(self, chat_id: int, message: str):
        if not hasattr(self, "loop") or self.loop is None:
            return
        asyncio.run_coroutine_threadsafe(
            self.app.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown"),
            self.loop
        )