"""
config.py — Central configuration for the weather pipeline.

Reads environment variables so that credentials are never hardcoded.
Values are loaded from a .env file when running locally, or from
Docker Compose environment blocks when running inside a container.
"""

import os
from dotenv import load_dotenv

# Load variables from a .env file if it exists (useful for local development)
load_dotenv()

# Database
DB_CONFIG = {
    "host":     os.getenv("POSTGRES_HOST", "localhost"),
    "port":     int(os.getenv("POSTGRES_PORT", 5432)),
    "dbname":   os.getenv("WEATHER_DB", "weather_db"),
    "user":     os.getenv("POSTGRES_USER", "airflow"),
    "password": os.getenv("POSTGRES_PASSWORD", "airflow"),
}

# Open-Meteo API
LATITUDE  = float(os.getenv("LATITUDE",  6.9271))   # Colombo, Sri Lanka
LONGITUDE = float(os.getenv("LONGITUDE", 79.8612))
CITY_NAME = os.getenv("CITY_NAME", "Colombo")

# Fields requested from the current-conditions endpoint
WEATHER_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "wind_speed_10m",
    "surface_pressure",
    "weather_code",
]

# Base URL for Open-Meteo current weather
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
