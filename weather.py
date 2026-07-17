import requests



class WeatherService:
    def __init__(self, latitude: float, longitude: float):
        self.lat = latitude
        self.lon = longitude
        self.api_url = "https://api.open-meteo.com/v1/forecast"

    @staticmethod
    def resolve_city(city_name: str):
        """Resolves a city name to (city_name, lat, lon) using Open-Meteo Geocoding API."""
        url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {
            "name": city_name,
            "count": 1,
            "language": "en",
            "format": "json"
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            results = data.get("results")
            if results:
                result = results[0]
                return {
                    "city": result.get("name"),
                    "latitude": result.get("latitude"),
                    "longitude": result.get("longitude")
                }
        except requests.RequestException as e:
            print(f"Geocoding Error: {e}")
            if e.response is not None:
                print(f"Status Code: {e.response.status_code}")
                print(f"Response Body: {e.response.text}")
        return None


    def get_forecast(self):
        """Fetches forecast data from Open-Meteo API."""
        params = {
            "latitude": self.lat,
            "longitude": self.lon,
            "current_weather": "true",
            "hourly": "precipitation_probability,temperature_2m,weathercode",
            "timezone": "auto"
        }
        try:
            response = requests.get(self.api_url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching weather data: {e}")
            if e.response is not None:
                print(f"Status Code: {e.response.status_code}")
                print(f"Response Body: {e.response.text}")
            return None

    def get_current_weather(self):
        """Extracts current weather parameters."""
        data = self.get_forecast()
        if data and "current_weather" in data:
            return data["current_weather"]
        return None

    def is_rain_expected(self):
        """Checks if precipitation probability exceeds 50% in the next 12 hours."""
        data = self.get_forecast()
        if not data or "hourly" not in data:
            return False

        probabilities = data["hourly"].get("precipitation_probability", [])[:12]
        for prob in probabilities:
            if prob > 50:
                return True
        return False

    def get_weather_data_formatted(self):
        """Formats weather parameters for prompt context."""
        data = self.get_forecast()
        if not data:
            return {"error": "Could not fetch data"}

        current = data.get("current_weather", {})
        hourly = data.get("hourly", {})

        temp_samples = hourly.get("temperature_2m", [])[:3]
        rain_prob_samples = hourly.get("precipitation_probability", [])[:3]

        return {
            "current_temp": current.get("temperature"),
            "windspeed": current.get("windspeed"),
            "weather_code": current.get("weathercode"),
            "next_hours_temp": temp_samples,
            "next_hours_rain_prob": rain_prob_samples
        }