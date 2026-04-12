import logging
import sys
from datetime import datetime, timezone

import requests

from .config import (
    CITY_NAME,
    LATITUDE,
    LONGITUDE,
    OPEN_METEO_URL,
    WEATHER_VARIABLES,
)
from .db_utils import create_table, insert_weather

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def fetch_weather() -> dict:
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "current": ",".join(WEATHER_VARIABLES),
        "timezone": "Asia/Colombo",
    }

    logger.info(f"Requesting weather data for {CITY_NAME} ({LATITUDE}, {LONGITUDE})")

    response = requests.get(OPEN_METEO_URL, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()
    logger.info("API response received successfully.")
    return data


def parse_weather(data: dict) -> dict:
    current = data.get("current")
    if not current:
        raise ValueError("'current' key missing from API response.")

    missing = [v for v in WEATHER_VARIABLES if v not in current]
    if missing:
        raise ValueError(f"Missing fields in API response: {missing}")

    record = {
        "extraction_timestamp": datetime.now(timezone.utc).replace(tzinfo=None),
        "city": CITY_NAME,
        "temperature_2m": current["temperature_2m"],
        "relative_humidity_2m": current["relative_humidity_2m"],
        "wind_speed_10m": current["wind_speed_10m"],
        "surface_pressure": current["surface_pressure"],
        "weather_code": int(current["weather_code"]),
    }

    logger.info(
        f"Parsed: temp={record['temperature_2m']}°C  "
        f"humidity={record['relative_humidity_2m']}%  "
        f"wind={record['wind_speed_10m']} km/h"
    )
    return record


def run():
    try:
        create_table()
        raw_data = fetch_weather()
        record = parse_weather(raw_data)
        insert_weather(record)
        logger.info("Pipeline completed successfully.")
        return 0

    except requests.exceptions.Timeout:
        logger.error("API request timed out after 10 seconds.")
        return 1

    except requests.exceptions.ConnectionError:
        logger.error("Failed to connect to the weather API.")
        return 1

    except requests.exceptions.HTTPError as e:
        logger.error(f"API returned an HTTP error: {e}")
        return 1

    except ValueError as e:
        logger.error(f"Data parsing error: {e}")
        return 1

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(run())