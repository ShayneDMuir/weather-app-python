# Weather App

A modern weather application built with Python and PyQt6.

## Quick Start (Windows)

Just download and run `dist/WeatherApp.exe` - no installation required!

## Features

- Real-time weather data from Open-Meteo API
- Auto-detects your location on startup
- Search for any location with autocomplete
- Animated weather icons
- Current conditions, temperature, min/max
- Weather details: humidity, wind, UV index, rainfall, sunrise/sunset
- "What to Wear" clothing suggestions based on conditions
- Material Design 3 interface

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
pyinstaller --onefile --windowed --name "WeatherApp" --add-data "animated;animated" main.py
```

The executable will be in the `dist/` folder.
