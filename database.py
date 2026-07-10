import psycopg2
from config import DB_URL, ALERT_DEFAULT_TIME


class Database:
    def __init__(self):
        self.conn = psycopg2.connect(DB_URL)
        self._create_table()

    def _create_table(self):
        """Creates the users table and active_users view if they do not exist."""
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    chat_id BIGINT PRIMARY KEY,
                    city VARCHAR(100) NOT NULL,
                    latitude DOUBLE PRECISION NOT NULL,
                    longitude DOUBLE PRECISION NOT NULL,
                    alert_time TIME DEFAULT %s,
                    subscribed BOOLEAN DEFAULT TRUE
                );
            """, (ALERT_DEFAULT_TIME,))

            cur.execute("""
                CREATE OR REPLACE VIEW active_users AS
                SELECT chat_id, city, latitude, longitude, alert_time
                FROM users
                WHERE subscribed = TRUE;
            """)
            self.conn.commit()

    def add_user(self, chat_id: int, city: str , lat: float, lon: float):
        """Adds a new user or updates/re-subscribes their location if they already exist."""
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO users 
                (chat_id, city, latitude, longitude, alert_time, subscribed)
                VALUES (%s, %s, %s, %s, %s, TRUE)
                ON CONFLICT (chat_id) DO UPDATE SET
                    city = EXCLUDED.city, 
                    latitude = EXCLUDED.latitude, 
                    longitude = EXCLUDED.longitude, 
                    subscribed = TRUE;
                """,(chat_id, city ,lat, lon, ALERT_DEFAULT_TIME,))
            self.conn.commit()



    def remove_user(self, chat_id: int):
        """Soft-deletes a user by setting subscribed = FALSE, stopping scheduled alerts."""
        with self.conn.cursor() as cursor:
            cursor.execute("""
                UPDATE users
                SET subscribed = FALSE
                WHERE chat_id = %s;
                """,(chat_id,))
            self.conn.commit()

    def update_location(self, chat_id: int, city: str, lat: float, lon: float):
        """Updates location parameters for a user and ensures they are subscribed."""
        with self.conn.cursor() as cursor:
            cursor.execute("""
                UPDATE users
                SET city = %s, latitude = %s, longitude = %s, subscribed = TRUE
                WHERE chat_id = %s;
                """, (city, lat, lon, chat_id,))
            self.conn.commit()
        

    def update_alert_time(self, chat_id: int, time_str: str):
        """Updates the daily alert delivery time for a user (HH:MM format)."""
        with self.conn.cursor() as cursor:
            cursor.execute("""
                UPDATE users
                SET alert_time = %s
                WHERE chat_id = %s;
                """, (time_str, chat_id,))
            self.conn.commit()

    def get_all_users(self):
        """Retrieves all active users as a list of dictionaries from the active_users view."""
        with self.conn.cursor() as cur:
            cur.execute("SELECT chat_id, city, latitude, longitude, alert_time FROM active_users;")
            rows = cur.fetchall()
            users = []
            for row in rows:
                users.append({
                    "chat_id": row[0],
                    "city": row[1],
                    "latitude": row[2],
                    "longitude": row[3],
                    "alert_time": row[4]
                })
            return users


    def get_users_grouped_by_city_and_time(self):
        """Groups active users by city and alert_time using aggregate function ARRAY_AGG."""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT city, latitude, longitude, alert_time, ARRAY_AGG(chat_id)
                FROM active_users
                GROUP BY city, latitude, longitude, alert_time;
            """)
            rows = cur.fetchall()
            groups = []
            for row in rows:
                groups.append({
                    "city": row[0],
                    "latitude": row[1],
                    "longitude": row[2],
                    "alert_time": row[3],
                    "chat_ids": row[4]
                })
            return groups

    def get_user(self, chat_id: int):
        """Retrieves a single user's parameters (checks base table to see opt-in status)."""
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT chat_id, city, latitude, longitude, alert_time, subscribed FROM users WHERE chat_id = %s;",
                (chat_id,))
            row = cur.fetchone()
            if row:
                return {
                    "chat_id": row[0],
                    "city": row[1],
                    "latitude": row[2],
                    "longitude": row[3],
                    "alert_time": row[4],
                    "subscribed": row[5]
                }
            return None

    def close(self):
        """Gracefully closes the database connection."""
        self.conn.close()