import schedule
import time
import datetime
from weather import WeatherService


class WeatherScheduler:
    def __init__(self, db, gemini, bot):
        self.db = db
        self.gemini = gemini
        self.bot = bot

    def send_daily_alerts(self):
        """Checks the current time and sends daily alerts to users matching their scheduled alert time."""
        ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        current_time_str = datetime.datetime.now(ist).strftime("%H:%M")


        city_groups = self.db.get_users_grouped_by_city_and_time()

        for group in city_groups:

            alert_time = group["alert_time"]
            if hasattr(alert_time, "strftime"):
                group_time_str = alert_time.strftime("%H:%M")
            else:
                group_time_str = str(alert_time)[:5]


            if group_time_str != current_time_str:
                continue

            display_city = group["city"]
            lat = group["latitude"]
            lon = group["longitude"]
            chat_ids = group["chat_ids"]

            weather_service = WeatherService(lat, lon)
            weather_data = weather_service.get_weather_data_formatted()

            if "error" in weather_data:
                continue

            rain_warning = ""
            if weather_service.is_rain_expected():
                rain_warning = "⚠️ *Rain Alert:* Rain is expected in the next few hours!\n\n"

            summary = self.gemini.generate_summary(weather_data, display_city)
            message_content = f"{rain_warning}{summary}"


            for chat_id in chat_ids:
                self.bot.send_message(chat_id, message_content)

    def start(self):
        """Starts the scheduling loop to check every minute."""
        schedule.every().minute.do(self.send_daily_alerts)
        while True:
            schedule.run_pending()
            time.sleep(1)