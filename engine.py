from groq import Groq
from config import GROQ_API_KEY


class GeminiSummary:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = "llama-3.1-8b-instant"

    def generate_summary(self, weather_data: dict, location: str) -> str:
        """Generates a conversational natural-language weather summary."""
        prompt = f"""
You are AtmosIQ, a smart and friendly weather assistant for Telegram.

Your task is to generate a short and accurate weather summary for users.

Location: {location}

Weather Data:
{weather_data}

Rules:
- Keep the response under 3 short sentences.
- Mention only important weather conditions (temperature, rain, wind, humidity, etc.).
- Give practical advice such as:
    - Carry an umbrella if rain is likely.
    - Wear light clothes if it is hot.
    - Wear warm clothes if it is cold.
    - Stay hydrated if temperatures are high.
    - Be cautious if strong winds or thunderstorms are expected.
- Never guess information that is not present in the weather data.
- Avoid technical weather terminology.
- Use a natural and conversational tone.
- Use at most one relevant emoji.
- Do not use markdown except **bold text** if necessary.
- Keep the message suitable for a Telegram notification.

Generate only the weather summary and nothing else.
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Groq error: {e}")
            return f"Current temperature is {weather_data.get('current_temp', 'N/A')}°C."

    def generate_alert(self, alert_type: str, weather_data: dict) -> str:
        """Generates severe weather warnings."""
        prompt = f"""
You are AtmosIQ, an intelligent weather alert system.

Generate a short and clear weather warning.

Alert Type:
{alert_type}

Weather Data:
{weather_data}

Rules:
- Keep the message to 1 or 2 short sentences.
- Clearly explain what weather condition triggered the alert.
- Tell the user what action they should take.
- Use simple language.
- Make the alert sound urgent but not alarming.
- Never exaggerate the weather conditions.
- Do not mention weather parameters unless useful.
- Use one appropriate weather emoji if relevant.
- Suitable for Telegram push notifications.
- Do not use markdown except **bold text**.

Examples:

Rain Alert:
"Rain is expected within the next few hours. Don't forget to carry an umbrella. ☔"

Heat Alert:
"High temperatures are expected today. Stay hydrated and avoid prolonged exposure to direct sunlight. ☀️"

Thunderstorm Alert:
"Thunderstorms may occur soon. Stay indoors if possible and avoid open areas. ⛈️"

Generate only the alert message.
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Groq error: {e}")
            return f"⚠️ Warning: Severe {alert_type} expected! Please take precautions."
