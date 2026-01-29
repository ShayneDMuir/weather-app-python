import requests

"""
Weather App - Main Entry Point
"""


def main():
    url = "https://api.open-meteo.com/v1/forecast"
    params = {"latitude": -36.8485, "longitude": 174.7633, "current_weather": True, "daily": "temperature_2m_max,temperature_2m_min,rain_sum,precipitation_probability_max,sunrise,sunset"}

    response = requests.get(url, params=params)
    data = response.json()
    weather = data["current_weather"]
    daily = data["daily"]
    from datetime import datetime

    print(f"{datetime.now()} Current temperature: {weather['temperature']}°C")
    print(f"Min temperature: {daily['temperature_2m_min'][0]}°C")
    print(f"Max temperature: {daily['temperature_2m_max'][0]}°C")
    print(f"Rainfall: {daily['rain_sum'][0]} mm")
    print(f"Max precipitation probability: {daily['precipitation_probability_max'][0]}%")
    print(f"Sunrise: {daily['sunrise'][0]}")
    print(f"Sunset: {daily['sunset'][0]}")


if __name__ == "__main__":
    main()
