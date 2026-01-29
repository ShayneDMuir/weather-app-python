import sys
import os
import requests
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtSvgWidgets import QSvgWidget

"""
Weather App - Main Entry Point
"""

ICON_DIR = os.path.join(os.path.dirname(__file__), "animated")


def get_weather_icon(code, is_day=True):
    day_icons = {
        0: "clear-day.svg",
        1: "fair-day.svg",
        2: "partly-cloudy-day.svg",
        3: "cloudy.svg",
        45: "fog.svg",
        48: "fog.svg",
        51: "rainy-1.svg",
        53: "rainy-2.svg",
        55: "rainy-3.svg",
        56: "rain-and-sleet-mix.svg",
        57: "rain-and-sleet-mix.svg",
        61: "rainy-1.svg",
        63: "rainy-3.svg",
        65: "rainy-6.svg",
        66: "rain-and-sleet-mix.svg",
        67: "rain-and-sleet-mix.svg",
        71: "snowy-1.svg",
        73: "snowy-3.svg",
        75: "snowy-6.svg",
        77: "snowy-2.svg",
        80: "rainy-1.svg",
        81: "rainy-3.svg",
        82: "rainy-6.svg",
        85: "snowy-4.svg",
        86: "snowy-6.svg",
        95: "thunder.svg",
        96: "severe-thunderstorm.svg",
        99: "severe-thunderstorm.svg"
    }
    night_icons = {
        0: "clear-night.svg",
        1: "fair-night.svg",
        2: "partly-cloudy-night.svg",
    }

    if not is_day and code in night_icons:
        icon = night_icons[code]
    else:
        icon = day_icons.get(code, "weather.svg")

    return os.path.join(ICON_DIR, icon)


def get_weather_description(code):
    descriptions = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Foggy",
        51: "Light drizzle",
        53: "Drizzle",
        55: "Dense drizzle",
        56: "Freezing drizzle",
        57: "Freezing drizzle",
        61: "Light rain",
        63: "Rain",
        65: "Heavy rain",
        66: "Freezing rain",
        67: "Freezing rain",
        71: "Light snow",
        73: "Snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Light showers",
        81: "Showers",
        82: "Heavy showers",
        85: "Snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with hail",
        99: "Thunderstorm with hail"
    }
    return descriptions.get(code, "Unknown")


def main():
    url = "https://api.open-meteo.com/v1/forecast"
    params = {"latitude": -36.8485, "longitude": 174.7633, "current_weather": True, "daily": "temperature_2m_max,temperature_2m_min,rain_sum,precipitation_probability_max,sunrise,sunset,weathercode"}

    response = requests.get(url, params=params)
    data = response.json()
    weather = data["current_weather"]
    daily = data["daily"]

    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle("Weather App")
    window.setFixedSize(450, 400)

    layout = QVBoxLayout()
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    # Title
    title = QLabel("Current Weather Information")
    title.setStyleSheet("color: #0066cc; font-size: 18px; font-weight: bold;")
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(title)

    # Location
    location = QLabel("Location: Auckland, New Zealand")
    location.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(location)

    # Weather icon
    is_day = weather.get("is_day", 1) == 1
    icon_path = get_weather_icon(weather['weathercode'], is_day)
    svg_widget = QSvgWidget(icon_path)
    svg_widget.setFixedSize(100, 100)
    layout.addWidget(svg_widget, alignment=Qt.AlignmentFlag.AlignCenter)

    # Weather info
    labels = [
        f"Conditions: {get_weather_description(weather['weathercode'])}",
        f"{datetime.now()}",
        f"Current temperature: {weather['temperature']}°C",
        f"Min temperature: {daily['temperature_2m_min'][0]}°C",
        f"Max temperature: {daily['temperature_2m_max'][0]}°C",
        f"Rainfall: {daily['rain_sum'][0]} mm",
        f"Max precipitation probability: {daily['precipitation_probability_max'][0]}%",
        f"Sunrise: {daily['sunrise'][0]}",
        f"Sunset: {daily['sunset'][0]}"
    ]
    for text in labels:
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

    layout.addStretch()
    window.setLayout(layout)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
