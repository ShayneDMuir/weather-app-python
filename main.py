import sys
import os
import requests
import geocoder
from geopy.geocoders import Nominatim
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                              QHBoxLayout, QFrame, QGraphicsDropShadowEffect,
                              QLineEdit, QCompleter, QListView, QScrollArea,
                              QSystemTrayIcon, QMenu)
from PyQt6.QtCore import Qt, QSize, QTimer, QStringListModel, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QAction
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


def get_current_location():
    """Get current location from IP address."""
    g = geocoder.ip('me')
    if g.ok:
        return g.latlng[0], g.latlng[1], g.city or "Unknown Location"
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
    response = requests.get(url, params=params)
    return response.json()


def get_stylesheet():
    """Return the Material Design 3 stylesheet."""
    return """
        QWidget#main {
            background-color: #f6f6f6;
        }
        QLabel {
            font-family: 'Roboto', 'Segoe UI', sans-serif;
            color: #1d1b20;
        }
        QLabel#location {
            font-size: 22px;
            font-weight: 400;
            color: #1d1b20;
        }
        QLabel#condition {
            font-size: 16px;
            font-weight: 400;
            color: #49454f;
        }
        QLabel#temperature {
            font-size: 64px;
            font-weight: 300;
            color: #1d1b20;
        }
        QLabel#minmax {
            font-size: 16px;
            font-weight: 500;
            color: #49454f;
        }
        QFrame#card {
            background-color: #ffffff;
            border-radius: 28px;
        }
        QLabel#cardTitle {
            font-size: 14px;
            font-weight: 500;
            color: #49454f;
            padding-bottom: 8px;
        }
        QLabel#detailLabel {
            font-size: 14px;
            font-weight: 400;
            color: #49454f;
        }
        QLabel#detailValue {
            font-size: 14px;
            font-weight: 500;
            color: #1d1b20;
        }
        QFrame#searchBar {
            background-color: #e6e0e9;
            border-radius: 28px;
        }
        QLineEdit#searchInput {
            font-family: 'Roboto', 'Segoe UI', sans-serif;
            font-size: 16px;
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
            border-radius: 28px;
        }
        QLabel#forecastDay {
            font-size: 12px;
            font-weight: 500;
            color: #49454f;
        }
        QLabel#forecastTemp {
            font-size: 14px;
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
    card_shadow.setBlurRadius(20)
    card_shadow.setOffset(0, 4)
    card_shadow.setColor(QColor(0, 0, 0, 25))
    card.setGraphicsEffect(card_shadow)

    card_layout = QVBoxLayout(card)
    card_layout.setContentsMargins(24, 16, 24, 16)
    card_layout.setSpacing(8)

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
    card_shadow.setBlurRadius(20)
    card_shadow.setOffset(0, 4)
    card_shadow.setColor(QColor(0, 0, 0, 25))
    card.setGraphicsEffect(card_shadow)

    card_layout = QVBoxLayout(card)
    card_layout.setContentsMargins(16, 16, 16, 16)
    card_layout.setSpacing(12)

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
        day_layout.setContentsMargins(4, 4, 4, 4)
        day_layout.setSpacing(4)
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
        icon.setFixedSize(32, 32)
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


def create_clothing_card(weather_data):
    """Create the clothing suggestions card widget."""
    suggestions = get_clothing_suggestions(weather_data)

    card = QFrame()
    card.setObjectName("card")

    card_shadow = QGraphicsDropShadowEffect()
    card_shadow.setBlurRadius(20)
    card_shadow.setOffset(0, 4)
    card_shadow.setColor(QColor(0, 0, 0, 25))
    card.setGraphicsEffect(card_shadow)

    card_layout = QVBoxLayout(card)
    card_layout.setContentsMargins(24, 16, 24, 16)
    card_layout.setSpacing(6)

    card_title = QLabel("What to Wear")
    card_title.setObjectName("cardTitle")
    card_layout.addWidget(card_title)

    for suggestion in suggestions:
        label = QLabel(f"• {suggestion}")
        label.setObjectName("detailLabel")
        card_layout.addWidget(label)

    return card


class WeatherApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("main")
        self.setWindowTitle("Weather")
        self.setMinimumSize(380, 600)
        self.resize(420, 900)
        self.setStyleSheet(get_stylesheet())

        # Get current location
        self.lat, self.lon, self.location_name = get_current_location()

        # Setup system tray
        self.setup_tray()

        # Main layout
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(0)

        # Search bar (Material Design 3 style)
        search_container = QFrame()
        search_container.setObjectName("searchBar")
        search_container.setFixedHeight(56)

        search_shadow = QGraphicsDropShadowEffect()
        search_shadow.setBlurRadius(12)
        search_shadow.setOffset(0, 2)
        search_shadow.setColor(QColor(0, 0, 0, 30))
        search_container.setGraphicsEffect(search_shadow)

        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(16, 0, 16, 0)
        search_layout.setSpacing(12)

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

        self.main_layout.addSpacing(16)

        # Scroll area for content
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("QScrollArea { background: transparent; } QScrollBar:vertical { width: 8px; background: transparent; } QScrollBar::handle:vertical { background: #cac4d0; border-radius: 4px; } QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }")

        # Content container with margins for shadows
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(8, 8, 8, 8)
        self.content_layout.setSpacing(0)

        self.scroll_area.setWidget(self.content_widget)
        self.main_layout.addWidget(self.scroll_area)

        self.setLayout(self.main_layout)

    def setup_tray(self):
        """Setup system tray icon and menu."""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip("Weather App")

        # Create tray menu
        tray_menu = QMenu()

        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show_window)
        tray_menu.addAction(show_action)

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_activated)

        # Use a default icon (or you could use one of your weather icons)
        icon_path = os.path.join(ICON_DIR, "weather.svg")
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))

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

        # Load weather data
        self.update_weather()

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
        weather = weather_data["current_weather"]
        daily = weather_data["daily"]

        # Location label
        location_label = QLabel(self.location_name)
        location_label.setObjectName("location")
        location_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(location_label)

        self.content_layout.addSpacing(8)

        # Condition
        condition = QLabel(get_weather_description(weather['weathercode']))
        condition.setObjectName("condition")
        condition.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(condition)

        self.content_layout.addSpacing(16)

        # Weather icon
        is_day = weather.get("is_day", 1) == 1
        icon_path = get_weather_icon(weather['weathercode'], is_day)
        svg_widget = QSvgWidget(icon_path)
        svg_widget.setFixedSize(140, 140)
        self.content_layout.addWidget(svg_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        self.content_layout.addSpacing(8)

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

        self.content_layout.addSpacing(24)

        # Details card
        card = create_details_card(weather_data)
        self.content_layout.addWidget(card)

        self.content_layout.addSpacing(16)

        # Clothing suggestions card
        clothing_card = create_clothing_card(weather_data)
        self.content_layout.addWidget(clothing_card)

        self.content_layout.addSpacing(16)

        # 7-day forecast card
        forecast_card = create_forecast_card(weather_data)
        self.content_layout.addWidget(forecast_card)

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
