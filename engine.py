from groq import Groq
from config import GROQ_API_KEY

class GeminiSummary:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = "llama-3.1-8b-instant"

    def generate_summary(self, weather_data: dict, location: str) -> str:
        """Generates a conversational natural-language weather summary."""
        prompt = (
            f"You are a friendly weather announcer bot.\n"
            f"Summarize the weather for {location} based on this data:\n"
            f"{weather_data}\n\n"
            f"Keep it under 3 sentences. Suggest what to wear or if they need an umbrella. "
            f"Do not use markdown other than *bold text*."
        )
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
        prompt = (
            f"Generate a critical, short weather warning for: {alert_type}.\n"
            f"Weather details: {weather_data}\n\n"
            f"Keep it to 1-2 sentences."
        )
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Groq error: {e}")
            return f"⚠️ Warning: Severe {alert_type} expected! Please take precautions."