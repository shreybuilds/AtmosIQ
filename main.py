from bot import WeatherBot
from scheduler import WeatherScheduler
import threading


def main():
    bot = WeatherBot()
    scheduler = WeatherScheduler(bot.db, bot.gemini, bot)

    thread = threading.Thread(target=scheduler.start)
    thread.daemon = True
    thread.start()

    try:
        bot.run()
    finally:
        bot.db.close()


if __name__ == "__main__":
    main()