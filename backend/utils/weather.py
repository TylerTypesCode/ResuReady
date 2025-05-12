from dotenv import load_dotenv
import requests
import os

load_dotenv()

def get_current_weather(city_name):
    api_key = os.getenv('WEATHER_API_KEY')

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city_name,
        "appid": api_key,
        "units": "metric"  # or 'imperial' for Fahrenheit
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Will raise an error if the request fails (non-2xx status code)
        data = response.json()

        # Check if the 'weather' key is in the response
        if 'weather' in data:
            temperature = round(data['main']['temp'])
            description = data['weather'][0]['main']  # e.g., 'Clear', 'Clouds'
            icon = data['weather'][0]['icon']         # e.g., '01d'

            return {
                "temperature": temperature,
                "description": description,
                "icon": icon
            }
        else:
            print("Error: 'weather' key not found in the response")
            return None

    except requests.RequestException as e:
        print(f"Error fetching weather: {e}")
        return None