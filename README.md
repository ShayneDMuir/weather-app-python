# Weather App

A modern weather application built with Python and PyQt6.

## Download

Download the latest `WeatherApp.exe` from [Releases](https://github.com/ShayneDMuir/weather-app-python/releases).

No installation required - just run the exe!

## Features

- Real-time weather data from Open-Meteo API
- Auto-detects your location on startup
- Search for any location with autocomplete
- 7-day forecast
- Animated weather icons
- Current conditions, temperature, min/max
- Weather details: humidity, wind, UV index, rainfall, sunrise/sunset
- "What to Wear" clothing suggestions based on conditions
- Material Design 3 interface

### System Tray

- Displays current temperature in the tray icon
- Minimize or close to hide to system tray
- Double-click tray icon to restore
- Right-click menu with options:
  - Fahrenheit/Celsius toggle
  - Run on startup
  - Check for updates

### Auto Features

- **Dark mode**: Automatically switches to dark theme after sunset
- **Auto-refresh**: Weather updates every 30 minutes
- **Auto-update**: Checks for new versions from GitHub Releases

## For Developers

### Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Run from source

```bash
python main.py
```

### Build executable

```bash
pip install pyinstaller
pyinstaller WeatherApp.spec
```

The executable will be in the `dist/` folder.
