import sys
import os

# Suppress Qt SVG warnings about unsupported filter elements
os.environ["QT_LOGGING_RULES"] = "qt.svg.warning=false"

import requests
import geocoder
import winreg
import subprocess
import tempfile
from geopy.geocoders import Nominatim
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                              QHBoxLayout, QFrame, QGraphicsDropShadowEffect,
                              QLineEdit, QCompleter, QListView, QScrollArea,
                              QSystemTrayIcon, QMenu, QMessageBox)
from PyQt6.QtCore import Qt, QSize, QTimer, QStringListModel, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QAction, QPixmap, QPainter, QFont
from PyQt6.QtSvgWidgets import QSvgWidget

# App info
APP_NAME = "WeatherApp"
APP_VERSION = "1.1.2"
GITHUB_REPO = "ShayneDMuir/weather-app-python"

"""
Weather App - Main Entry Point
"""

ICON_DIR = os.path.join(os.path.dirname(__file__), "animated")


def check_for_updates():
    """Check GitHub releases for a newer version."""
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            latest_version = data.get("tag_name", "").lstrip("v")
            download_url = None
            for asset in data.get("assets", []):
                if asset["name"].endswith(".exe"):
                    download_url = asset["browser_download_url"]
                    break
            return latest_version, download_url
    except Exception:
        pass
    return None, None


def compare_versions(current, latest):
    """Return True if latest is newer than current."""
    try:
        current_parts = [int(x) for x in current.split(".")]
        latest_parts = [int(x) for x in latest.split(".")]
        return latest_parts > current_parts
    except Exception:
        return False


def download_update(download_url, progress_callback=None):
    """Download the update to a temp file."""
    try:
        response = requests.get(download_url, stream=True, timeout=60)
        if response.status_code == 200:
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, "WeatherApp_update.exe")
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total_size:
                        progress_callback(int(downloaded * 100 / total_size))
            return temp_path
    except Exception:
        pass
    return None


def apply_update(new_exe_path):
    """Create a batch script to replace the exe after app closes."""
    if not getattr(sys, 'frozen', False):
        return False  # Only works for frozen exe

    current_exe = sys.executable
    batch_path = os.path.join(tempfile.gettempdir(), "weather_update.bat")

    batch_content = f'''@echo off
timeout /t 2 /nobreak >nul
del "{current_exe}"
move "{new_exe_path}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
'''

    with open(batch_path, 'w') as f:
        f.write(batch_content)

    subprocess.Popen(['cmd', '/c', batch_path],
                     creationflags=subprocess.CREATE_NO_WINDOW)
    return True


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


def get_current_location():
    """Get current location from IP address."""
    try:
        g = geocoder.ip('me')
        if g.ok:
            return g.latlng[0], g.latlng[1], g.city or "Unknown Location"
    except Exception:
        pass
    return -36.8485, 174.7633, "Auckland, New Zealand"


def search_location(query):
    """Search for a location by name and return coordinates."""
    geolocator = Nominatim(user_agent="weather-app-python")
    location = geolocator.geocode(query)
    if location:
        return location.latitude, location.longitude, location.address
    return None


def fetch_location_suggestions(query):
    """Fetch location suggestions from Open-Meteo Geocoding API."""
    if len(query) < 2:
        return []

    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": query, "count": 5, "language": "en", "format": "json"}

    try:
        response = requests.get(url, params=params, timeout=3)
        data = response.json()

        if "results" not in data:
            return []

        suggestions = []
        for result in data["results"]:
            name = result.get("name", "")
            admin1 = result.get("admin1", "")
            country = result.get("country", "")

            # Build display name
            parts = [name]
            if admin1:
                parts.append(admin1)
            if country:
                parts.append(country)
            display_name = ", ".join(parts)

            suggestions.append({
                "display": display_name,
                "lat": result["latitude"],
                "lon": result["longitude"],
                "name": f"{name}, {country}" if country else name
            })

        return suggestions
    except Exception:
        return []


def fetch_weather_data(lat, lon):
    """Fetch weather data from Open-Meteo API."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        "daily": "temperature_2m_max,temperature_2m_min,rain_sum,precipitation_probability_max,sunrise,sunset,weathercode,uv_index_max",
        "hourly": "relative_humidity_2m,wind_speed_10m",
        "timezone": "auto"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    except Exception:
        return None


def get_stylesheet(dark_mode=False):
    """Return the Material Design 3 stylesheet."""
    if dark_mode:
        # Dark mode colors
        return """
            QWidget#main {
                background-color: #1a1a2e;
            }
            QLabel {
                font-family: 'Roboto', 'Segoe UI', sans-serif;
                color: #e6e1e5;
            }
            QLabel#location {
                font-size: 18px;
                font-weight: 400;
                color: #e6e1e5;
            }
            QLabel#condition {
                font-size: 14px;
                font-weight: 400;
                color: #cac4d0;
            }
            QLabel#temperature {
                font-size: 48px;
                font-weight: 300;
                color: #e6e1e5;
            }
            QLabel#minmax {
                font-size: 14px;
                font-weight: 500;
                color: #cac4d0;
            }
            QFrame#card {
                background-color: #2d2d44;
                border-radius: 20px;
            }
            QLabel#cardTitle {
                font-size: 12px;
                font-weight: 500;
                color: #cac4d0;
                padding-bottom: 4px;
            }
            QLabel#detailLabel {
                font-size: 12px;
                font-weight: 400;
                color: #cac4d0;
            }
            QLabel#detailValue {
                font-size: 12px;
                font-weight: 500;
                color: #e6e1e5;
            }
            QFrame#searchBar {
                background-color: #2d2d44;
                border-radius: 22px;
            }
            QLineEdit#searchInput {
                font-family: 'Roboto', 'Segoe UI', sans-serif;
                font-size: 14px;
                padding: 0px;
                border: none;
                background-color: transparent;
                color: #e6e1e5;
            }
            QLineEdit#searchInput:focus {
                outline: none;
            }
            QLabel#searchIcon {
                color: #cac4d0;
                font-size: 18px;
            }
            QListView {
                font-family: 'Roboto', 'Segoe UI', sans-serif;
                font-size: 14px;
                background-color: #2d2d44;
                border: 1px solid #49454f;
                border-radius: 4px;
                padding: 4px 0;
                outline: none;
                margin-top: 4px;
            }
            QListView::item {
                padding: 14px 16px;
                color: #e6e1e5;
                border: none;
                min-height: 24px;
            }
            QListView::item:hover {
                background-color: #3d3d5c;
            }
            QListView::item:selected {
                background-color: #4a4458;
                color: #e6e1e5;
            }
            QFrame#forecastCard {
                background-color: #2d2d44;
                border-radius: 20px;
            }
            QLabel#forecastDay {
                font-size: 10px;
                font-weight: 500;
                color: #cac4d0;
            }
            QLabel#forecastTemp {
                font-size: 12px;
                font-weight: 500;
                color: #e6e1e5;
            }
        """
    else:
        # Light mode colors
        return """
            QWidget#main {
                background-color: #f6f6f6;
            }
            QLabel {
                font-family: 'Roboto', 'Segoe UI', sans-serif;
                color: #1d1b20;
            }
            QLabel#location {
                font-size: 18px;
                font-weight: 400;
                color: #1d1b20;
            }
            QLabel#condition {
                font-size: 14px;
                font-weight: 400;
                color: #49454f;
            }
            QLabel#temperature {
                font-size: 48px;
                font-weight: 300;
                color: #1d1b20;
            }
            QLabel#minmax {
                font-size: 14px;
                font-weight: 500;
                color: #49454f;
            }
            QFrame#card {
                background-color: #ffffff;
                border-radius: 20px;
            }
            QLabel#cardTitle {
                font-size: 12px;
                font-weight: 500;
                color: #49454f;
                padding-bottom: 4px;
            }
            QLabel#detailLabel {
                font-size: 12px;
                font-weight: 400;
                color: #49454f;
            }
            QLabel#detailValue {
                font-size: 12px;
                font-weight: 500;
                color: #1d1b20;
            }
            QFrame#searchBar {
                background-color: #e6e0e9;
                border-radius: 22px;
            }
            QLineEdit#searchInput {
                font-family: 'Roboto', 'Segoe UI', sans-serif;
                font-size: 14px;
                padding: 0px;
                border: none;
                background-color: transparent;
                color: #1d1b20;
            }
            QLineEdit#searchInput:focus {
                outline: none;
            }
            QLabel#searchIcon {
                color: #49454f;
                font-size: 18px;
            }
            QListView {
                font-family: 'Roboto', 'Segoe UI', sans-serif;
                font-size: 14px;
                background-color: #f3edf7;
                border: 1px solid #cac4d0;
                border-radius: 4px;
                padding: 4px 0;
                outline: none;
                margin-top: 4px;
            }
            QListView::item {
                padding: 14px 16px;
                color: #1d1b20;
                border: none;
                min-height: 24px;
            }
            QListView::item:hover {
                background-color: #e7e0ec;
            }
            QListView::item:selected {
                background-color: #d0bcff;
                color: #21005d;
            }
            QFrame#forecastCard {
                background-color: #ffffff;
                border-radius: 20px;
            }
            QLabel#forecastDay {
                font-size: 10px;
                font-weight: 500;
                color: #49454f;
            }
            QLabel#forecastTemp {
                font-size: 12px;
                font-weight: 500;
                color: #1d1b20;
            }
        """


def create_details_card(weather_data):
    """Create the weather details card widget."""
    daily = weather_data["daily"]
    hourly = weather_data["hourly"]

    card = QFrame()
    card.setObjectName("card")

    card_shadow = QGraphicsDropShadowEffect()
    card_shadow.setBlurRadius(16)
    card_shadow.setOffset(0, 3)
    card_shadow.setColor(QColor(0, 0, 0, 30))
    card.setGraphicsEffect(card_shadow)

    card_layout = QVBoxLayout(card)
    card_layout.setContentsMargins(16, 12, 16, 12)
    card_layout.setSpacing(4)

    card_title = QLabel("Weather Details")
    card_title.setObjectName("cardTitle")
    card_layout.addWidget(card_title)

    details_data = [
        ("Humidity", f"{hourly['relative_humidity_2m'][0]}%"),
        ("Wind", f"{hourly['wind_speed_10m'][0]} km/h"),
        ("UV Index", f"{daily['uv_index_max'][0]}"),
        ("Rainfall", f"{daily['rain_sum'][0]} mm"),
        ("Precipitation", f"{daily['precipitation_probability_max'][0]}%"),
        ("Sunrise", daily['sunrise'][0].split('T')[1]),
        ("Sunset", daily['sunset'][0].split('T')[1])
    ]

    for label_text, value_text in details_data:
        row = QHBoxLayout()
        row.setSpacing(0)

        label = QLabel(label_text)
        label.setObjectName("detailLabel")

        value = QLabel(value_text)
        value.setObjectName("detailValue")
        value.setAlignment(Qt.AlignmentFlag.AlignRight)

        row.addWidget(label)
        row.addWidget(value)
        card_layout.addLayout(row)

    return card


def get_clothing_suggestions(weather_data):
    """Generate clothing suggestions based on weather conditions."""
    weather = weather_data["current_weather"]
    daily = weather_data["daily"]
    hourly = weather_data["hourly"]

    temp = weather["temperature"]
    wind_speed = hourly["wind_speed_10m"][0]
    precipitation_chance = daily["precipitation_probability_max"][0]
    uv_index = daily["uv_index_max"][0]

    # Calculate is_day from sunrise/sunset times (more accurate than API flag)
    current_time = weather.get("time", "")
    sunrise = daily["sunrise"][0] if daily.get("sunrise") else ""
    sunset = daily["sunset"][0] if daily.get("sunset") else ""

    is_day = False
    if current_time and sunrise and sunset:
        is_day = sunrise <= current_time <= sunset

    suggestions = []

    # Temperature-based suggestions
    if temp <= 5:
        suggestions.append("Heavy winter coat")
        suggestions.append("Warm layers & thermals")
        suggestions.append("Scarf, gloves & beanie")
    elif temp <= 12:
        suggestions.append("Warm jacket or coat")
        suggestions.append("Long sleeves & layers")
        suggestions.append("Light scarf")
    elif temp <= 18:
        suggestions.append("Light jacket or sweater")
        suggestions.append("Long pants")
    elif temp <= 24:
        suggestions.append("T-shirt or light top")
        suggestions.append("Light pants or jeans")
    else:
        suggestions.append("Light, breathable clothing")
        suggestions.append("Shorts or light dress")

    # Rain protection
    if precipitation_chance >= 50:
        suggestions.append("Umbrella")
        suggestions.append("Waterproof jacket")
    elif precipitation_chance >= 30:
        suggestions.append("Umbrella (just in case)")

    # Wind consideration
    if wind_speed >= 30:
        suggestions.append("Windbreaker")
    elif wind_speed >= 20 and temp <= 15:
        suggestions.append("Wind-resistant layer")

    # UV protection (only during daytime)
    if is_day:
        if uv_index >= 6:
            suggestions.append("Sunglasses")
            suggestions.append("Sunscreen")
            suggestions.append("Hat for sun protection")
        elif uv_index >= 3:
            suggestions.append("Sunglasses")

    return suggestions


def create_forecast_card(weather_data):
    """Create the 7-day forecast card widget."""
    daily = weather_data["daily"]

    card = QFrame()
    card.setObjectName("forecastCard")

    card_shadow = QGraphicsDropShadowEffect()
    card_shadow.setBlurRadius(16)
    card_shadow.setOffset(0, 3)
    card_shadow.setColor(QColor(0, 0, 0, 30))
    card.setGraphicsEffect(card_shadow)

    card_layout = QVBoxLayout(card)
    card_layout.setContentsMargins(12, 10, 12, 10)
    card_layout.setSpacing(6)

    # Card title
    card_title = QLabel("7-Day Forecast")
    card_title.setObjectName("cardTitle")
    card_layout.addWidget(card_title)

    # Horizontal row of days
    days_layout = QHBoxLayout()
    days_layout.setSpacing(4)

    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    for i in range(min(7, len(daily.get("time", [])))):
        day_widget = QWidget()
        day_layout = QVBoxLayout(day_widget)
        day_layout.setContentsMargins(2, 2, 2, 2)
        day_layout.setSpacing(2)
        day_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Get day name from date
        date_str = daily["time"][i]
        from datetime import datetime
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        day_name = day_names[date_obj.weekday()]

        # Day label
        day_label = QLabel(day_name)
        day_label.setObjectName("forecastDay")
        day_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        day_layout.addWidget(day_label)

        # Weather icon (smaller)
        weathercode = daily["weathercode"][i]
        icon_path = get_weather_icon(weathercode, is_day=True)
        icon = QSvgWidget(icon_path)
        icon.setFixedSize(24, 24)
        day_layout.addWidget(icon, alignment=Qt.AlignmentFlag.AlignCenter)

        # High temp
        high_temp = int(daily["temperature_2m_max"][i])
        temp_label = QLabel(f"{high_temp}°")
        temp_label.setObjectName("forecastTemp")
        temp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        day_layout.addWidget(temp_label)

        days_layout.addWidget(day_widget)

    card_layout.addLayout(days_layout)
    return card


class SuggestionWorker(QThread):
    """Worker thread for fetching location suggestions."""
    finished = pyqtSignal(list)

    def __init__(self, query):
        super().__init__()
        self.query = query

    def run(self):
        suggestions = fetch_location_suggestions(self.query)
        self.finished.emit(suggestions)


class UpdateWorker(QThread):
    """Worker thread for checking and downloading updates."""
    update_available = pyqtSignal(str, str)  # version, download_url
    download_complete = pyqtSignal(str)  # temp_path
    download_progress = pyqtSignal(int)  # percentage
    no_update = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, download_url=None):
        super().__init__()
        self.download_url = download_url

    def run(self):
        if self.download_url:
            # Download mode
            temp_path = download_update(self.download_url, self.download_progress.emit)
            if temp_path:
                self.download_complete.emit(temp_path)
            else:
                self.error.emit("Download failed")
        else:
            # Check mode
            latest_version, download_url = check_for_updates()
            if latest_version and compare_versions(APP_VERSION, latest_version):
                self.update_available.emit(latest_version, download_url)
            else:
                self.no_update.emit()


def create_clothing_card(weather_data):
    """Create the clothing suggestions card widget."""
    suggestions = get_clothing_suggestions(weather_data)

    card = QFrame()
    card.setObjectName("card")

    card_shadow = QGraphicsDropShadowEffect()
    card_shadow.setBlurRadius(16)
    card_shadow.setOffset(0, 3)
    card_shadow.setColor(QColor(0, 0, 0, 30))
    card.setGraphicsEffect(card_shadow)

    card_layout = QVBoxLayout(card)
    card_layout.setContentsMargins(16, 12, 16, 12)
    card_layout.setSpacing(3)

    card_title = QLabel("What to Wear")
    card_title.setObjectName("cardTitle")
    card_layout.addWidget(card_title)

    for suggestion in suggestions:
        label = QLabel(f"• {suggestion}")
        label.setObjectName("detailLabel")
        card_layout.addWidget(label)

    return card


class WeatherApp(QWidget):
    # Mobile phone aspect ratio (9:19.5 like iPhone)
    ASPECT_RATIO = 9 / 19.5

    def __init__(self):
        super().__init__()
        self.setObjectName("main")
        self.setWindowTitle("Weather")
        self.resize(390, 844)
        self.setMinimumSize(292, 633)  # Minimum size maintaining ratio

        # Dark mode tracking
        self.is_dark_mode = False
        self.sunrise = None
        self.sunset = None
        self.setStyleSheet(get_stylesheet(self.is_dark_mode))

        # Get current location
        self.lat, self.lon, self.location_name = get_current_location()

        # Setup system tray
        self.setup_tray()

        # Main layout
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(0)

        # Search bar (Material Design 3 style)
        search_container = QFrame()
        search_container.setObjectName("searchBar")
        search_container.setFixedHeight(44)

        search_shadow = QGraphicsDropShadowEffect()
        search_shadow.setBlurRadius(8)
        search_shadow.setOffset(0, 2)
        search_shadow.setColor(QColor(0, 0, 0, 25))
        search_container.setGraphicsEffect(search_shadow)

        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(12, 0, 12, 0)
        search_layout.setSpacing(8)

        # Search icon (using Unicode)
        search_icon = QLabel("\U0001F50D")
        search_icon.setObjectName("searchIcon")
        search_icon.setFixedSize(24, 24)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("Search location")
        self.search_input.returnPressed.connect(self.on_search)

        # Autocomplete setup
        self.location_cache = {}  # Store location data by display name
        self.completer_model = QStringListModel()
        self.completer = QCompleter(self.completer_model, self)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)

        # Style the popup
        popup = self.completer.popup()
        popup.setStyleSheet(get_stylesheet())

        self.search_input.setCompleter(self.completer)
        self.completer.activated.connect(self.on_suggestion_selected)

        # Debounce timer for search suggestions
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.fetch_suggestions)
        self.search_input.textChanged.connect(self.on_text_changed)

        search_layout.addWidget(search_icon)
        search_layout.addWidget(self.search_input)

        self.main_layout.addWidget(search_container)

        self.main_layout.addSpacing(12)

        # Content layout with margins for shadows
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(8, 0, 8, 8)
        self.content_layout.setSpacing(0)
        self.main_layout.addLayout(self.content_layout)

        self.setLayout(self.main_layout)

        # Load weather data
        self.update_weather()

        # Timer to check for day/night theme changes every minute
        self.theme_timer = QTimer()
        self.theme_timer.timeout.connect(self.check_theme)
        self.theme_timer.start(60000)  # Check every minute

        # Timer to refresh weather data every 30 minutes
        self.weather_timer = QTimer()
        self.weather_timer.timeout.connect(self.update_weather)
        self.weather_timer.start(1800000)  # 30 minutes

    def setup_tray(self):
        """Setup system tray icon and menu."""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip("Weather App")

        # Create tray menu
        tray_menu = QMenu()

        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show_window)
        tray_menu.addAction(show_action)

        tray_menu.addSeparator()

        # Run on startup toggle
        self.startup_action = QAction("Run on startup", self)
        self.startup_action.setCheckable(True)
        self.startup_action.setChecked(self.is_startup_enabled())
        self.startup_action.triggered.connect(self.toggle_startup)
        tray_menu.addAction(self.startup_action)

        # Check for updates
        self.update_action = QAction("Check for updates", self)
        self.update_action.triggered.connect(self.check_for_updates)
        tray_menu.addAction(self.update_action)

        tray_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_activated)

        # Set initial icon (will be updated with temperature)
        self.update_tray_icon(None)

        # Check for updates on startup (after a short delay)
        QTimer.singleShot(3000, self.silent_update_check)

    def get_exe_path(self):
        """Get the path to the executable."""
        if getattr(sys, 'frozen', False):
            return sys.executable
        return os.path.abspath(sys.argv[0])

    def is_startup_enabled(self):
        """Check if app is set to run on startup."""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_READ
            )
            winreg.QueryValueEx(key, APP_NAME)
            winreg.CloseKey(key)
            return True
        except WindowsError:
            return False

    def toggle_startup(self, checked):
        """Enable or disable run on startup."""
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        if checked:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, self.get_exe_path())
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except WindowsError:
                pass
        winreg.CloseKey(key)

    def update_tray_icon(self, temperature):
        """Update tray icon to show current temperature."""
        size = 64
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if temperature is not None:
            # Draw temperature text in white
            temp_text = f"{int(temperature)}°"
            font = QFont("Segoe UI", 28, QFont.Weight.Bold)
            painter.setFont(font)
            painter.setPen(QColor("#ffffff"))
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, temp_text)
        else:
            # Draw placeholder in white
            font = QFont("Segoe UI", 24, QFont.Weight.Bold)
            painter.setFont(font)
            painter.setPen(QColor("#ffffff"))
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "--")

        painter.end()
        self.tray_icon.setIcon(QIcon(pixmap))

    def check_theme(self):
        """Check if theme should change based on sunrise/sunset."""
        if not self.sunrise or not self.sunset:
            return

        from datetime import datetime

        try:
            # Get current time in same format as API (ISO format)
            now = datetime.now()
            current_time = now.strftime("%Y-%m-%dT%H:%M")

            # Compare with sunrise/sunset
            should_be_dark = current_time < self.sunrise or current_time >= self.sunset

            if should_be_dark != self.is_dark_mode:
                self.is_dark_mode = should_be_dark
                self.setStyleSheet(get_stylesheet(self.is_dark_mode))
                # Update completer popup style too
                if hasattr(self, 'completer'):
                    self.completer.popup().setStyleSheet(get_stylesheet(self.is_dark_mode))
        except Exception:
            pass

    def silent_update_check(self):
        """Check for updates silently on startup."""
        self.update_worker = UpdateWorker()
        self.update_worker.update_available.connect(self.on_update_available_silent)
        self.update_worker.start()

    def check_for_updates(self):
        """Manual check for updates from menu."""
        self.update_action.setEnabled(False)
        self.update_action.setText("Checking...")
        self.update_worker = UpdateWorker()
        self.update_worker.update_available.connect(self.on_update_available)
        self.update_worker.no_update.connect(self.on_no_update)
        self.update_worker.start()

    def on_update_available_silent(self, version, download_url):
        """Handle update available (silent check)."""
        self.tray_icon.showMessage(
            "Update Available",
            f"Version {version} is available. Right-click tray icon to update.",
            QSystemTrayIcon.MessageIcon.Information,
            5000
        )
        self.pending_update_url = download_url
        self.pending_update_version = version
        self.update_action.setText(f"Update to v{version}")

    def on_update_available(self, version, download_url):
        """Handle update available (manual check)."""
        self.update_action.setEnabled(True)
        reply = QMessageBox.question(
            self,
            "Update Available",
            f"Version {version} is available (current: {APP_VERSION}).\n\nDownload and install now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.download_update(download_url)
        else:
            self.pending_update_url = download_url
            self.pending_update_version = version
            self.update_action.setText(f"Update to v{version}")

    def on_no_update(self):
        """Handle no update available."""
        self.update_action.setEnabled(True)
        self.update_action.setText("Check for updates")
        self.tray_icon.showMessage(
            "No Updates",
            f"You're running the latest version ({APP_VERSION}).",
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )

    def download_update(self, download_url):
        """Download and install the update."""
        self.update_action.setEnabled(False)
        self.update_action.setText("Downloading...")
        self.download_worker = UpdateWorker(download_url)
        self.download_worker.download_progress.connect(self.on_download_progress)
        self.download_worker.download_complete.connect(self.on_download_complete)
        self.download_worker.error.connect(self.on_download_error)
        self.download_worker.start()

    def on_download_progress(self, percent):
        """Update download progress."""
        self.update_action.setText(f"Downloading... {percent}%")

    def on_download_complete(self, temp_path):
        """Handle download complete."""
        self.update_action.setText("Installing...")
        if apply_update(temp_path):
            self.tray_icon.showMessage(
                "Update Installing",
                "The app will restart shortly.",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
            QTimer.singleShot(1000, QApplication.instance().quit)
        else:
            self.update_action.setEnabled(True)
            self.update_action.setText("Check for updates")
            QMessageBox.warning(
                self,
                "Update Failed",
                "Could not apply update. Please download manually from GitHub."
            )

    def on_download_error(self, error):
        """Handle download error."""
        self.update_action.setEnabled(True)
        self.update_action.setText("Check for updates")
        self.tray_icon.showMessage(
            "Update Failed",
            error,
            QSystemTrayIcon.MessageIcon.Warning,
            3000
        )

    def show_window(self):
        """Show and activate the window."""
        self.showNormal()
        self.activateWindow()

    def tray_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()

    def changeEvent(self, event):
        """Handle window state changes."""
        if event.type() == event.Type.WindowStateChange:
            if self.isMinimized():
                self.hide()
                self.tray_icon.show()
                self.tray_icon.showMessage(
                    "Weather App",
                    "Running in background. Double-click to restore.",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000
                )
        super().changeEvent(event)

    def resizeEvent(self, event):
        """Lock aspect ratio during resize."""
        new_size = event.size()
        new_width = new_size.width()
        new_height = int(new_width / self.ASPECT_RATIO)

        if new_height != new_size.height():
            self.resize(new_width, new_height)
        super().resizeEvent(event)

    def update_weather(self):
        """Fetch and display weather data."""
        # Clear existing content
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

        # Fetch data
        weather_data = fetch_weather_data(self.lat, self.lon)

        # Handle connection error
        if weather_data is None:
            error_label = QLabel("Unable to connect")
            error_label.setObjectName("location")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.content_layout.addWidget(error_label)

            error_msg = QLabel("Check your internet connection\nand try again")
            error_msg.setObjectName("condition")
            error_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.content_layout.addWidget(error_msg)

            self.content_layout.addStretch()
            return

        weather = weather_data["current_weather"]
        daily = weather_data["daily"]

        # Store sunrise/sunset for theme switching
        self.sunrise = daily.get("sunrise", [None])[0]
        self.sunset = daily.get("sunset", [None])[0]

        # Check and apply theme based on time
        self.check_theme()

        # Update tray icon with current temperature
        self.update_tray_icon(weather["temperature"])
        self.tray_icon.setToolTip(f"{self.location_name}: {int(weather['temperature'])}°")

        # Location label
        location_label = QLabel(self.location_name)
        location_label.setObjectName("location")
        location_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(location_label)

        self.content_layout.addSpacing(4)

        # Condition
        condition = QLabel(get_weather_description(weather['weathercode']))
        condition.setObjectName("condition")
        condition.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(condition)

        self.content_layout.addSpacing(8)

        # Weather icon
        is_day = weather.get("is_day", 1) == 1
        icon_path = get_weather_icon(weather['weathercode'], is_day)
        svg_widget = QSvgWidget(icon_path)
        svg_widget.setFixedSize(100, 100)
        self.content_layout.addWidget(svg_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        self.content_layout.addSpacing(4)

        # Temperature
        temp = QLabel(f"{int(weather['temperature'])}°")
        temp.setObjectName("temperature")
        temp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(temp)

        # Min/Max
        minmax = QLabel(f"H:{int(daily['temperature_2m_max'][0])}°  L:{int(daily['temperature_2m_min'][0])}°")
        minmax.setObjectName("minmax")
        minmax.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(minmax)

        self.content_layout.addSpacing(12)

        # Details card
        card = create_details_card(weather_data)
        self.content_layout.addWidget(card)

        self.content_layout.addSpacing(10)

        # Clothing suggestions card
        clothing_card = create_clothing_card(weather_data)
        self.content_layout.addWidget(clothing_card)

        self.content_layout.addSpacing(10)

        # 7-day forecast card
        forecast_card = create_forecast_card(weather_data)
        self.content_layout.addWidget(forecast_card)

        # Add stretch to push content up
        self.content_layout.addStretch()

    def clear_layout(self, layout):
        """Recursively clear a layout."""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

    def on_text_changed(self, text):
        """Handle text changes with debouncing."""
        self.search_timer.stop()
        if len(text) >= 2:
            self.search_timer.start(400)  # 400ms debounce

    def fetch_suggestions(self):
        """Fetch and display location suggestions asynchronously."""
        query = self.search_input.text().strip()
        if len(query) < 2:
            return

        # Cancel any existing worker
        if hasattr(self, 'suggestion_worker') and self.suggestion_worker.isRunning():
            self.suggestion_worker.terminate()
            self.suggestion_worker.wait()

        # Start new worker thread
        self.suggestion_worker = SuggestionWorker(query)
        self.suggestion_worker.finished.connect(self.on_suggestions_received)
        self.suggestion_worker.start()

    def on_suggestions_received(self, suggestions):
        """Handle suggestions received from worker thread."""
        self.location_cache.clear()

        display_names = []
        for suggestion in suggestions:
            display_name = suggestion["display"]
            display_names.append(display_name)
            self.location_cache[display_name.lower()] = suggestion

        self.completer_model.setStringList(display_names)

    def on_suggestion_selected(self, text):
        """Handle selection from autocomplete dropdown."""
        key = text.lower()
        if key in self.location_cache:
            location = self.location_cache[key]
            self.lat = location["lat"]
            self.lon = location["lon"]
            self.location_name = location["name"]
            self.update_weather()
            self.search_input.clear()

    def on_search(self):
        """Handle enter press for manual search."""
        query = self.search_input.text().strip()
        if not query:
            return

        # Check if it's a cached suggestion first (case insensitive)
        if query.lower() in self.location_cache:
            self.on_suggestion_selected(query)
            return

        # Otherwise do a full search
        result = search_location(query)
        if result:
            self.lat, self.lon, self.location_name = result
            if len(self.location_name) > 40:
                parts = self.location_name.split(',')
                self.location_name = ', '.join(parts[:2])
            self.update_weather()
            self.search_input.clear()


def main():
    app = QApplication(sys.argv)
    window = WeatherApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
