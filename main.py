from bot import WeatherBot
from scheduler import WeatherScheduler
import threading
import os
import http.server
import socketserver

# A simple HTTP server to satisfy Render's port binding requirement
def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    # Prevent port collision issues
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Health check server running on port {port}")
        httpd.serve_forever()

def main():
    # Start the health check web server in a background thread
    web_thread = threading.Thread(target=run_health_server)
    web_thread.daemon = True
    web_thread.start()

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
