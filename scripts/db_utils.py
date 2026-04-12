import logging
import psycopg2

# Relative import 
from .config import DB_CONFIG

logger = logging.getLogger(__name__)


def get_connection():
    """
    Return an open psycopg2 connection using settings from config.py.
    Raises an exception if the connection fails (e.g. wrong host/password).
    """
    conn = psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        dbname=DB_CONFIG["dbname"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
    )
    return conn


def create_table():
    """Create the weather_data table if it doesn't exist."""
    
    create_sql = """
        CREATE TABLE IF NOT EXISTS weather_data (
            id SERIAL PRIMARY KEY,
            extraction_timestamp TIMESTAMP NOT NULL,
            city VARCHAR(100) NOT NULL,
            temperature_2m FLOAT NOT NULL,
            relative_humidity_2m FLOAT NOT NULL,
            wind_speed_10m FLOAT,
            surface_pressure FLOAT,
            weather_code INT
        );
    """

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(create_sql)
        logger.info("Table 'weather_data' is ready.")

    except Exception as e:
        logger.error(f"Failed to create table: {e}")
        raise


def insert_weather(record: dict):
    """Insert a weather record into the database. Expects a dict with keys:
    - extraction_timestamp (datetime)
    - city (str)
    - temperature_2m (float)
    - relative_humidity_2m (float)
    - wind_speed_10m (float)
    - surface_pressure (float)
    - weather_code (int)
    """
    
    insert_sql = """
        INSERT INTO weather_data (
            extraction_timestamp,
            city,
            temperature_2m,
            relative_humidity_2m,
            wind_speed_10m,
            surface_pressure,
            weather_code
        ) VALUES (
            %(extraction_timestamp)s,
            %(city)s,
            %(temperature_2m)s,
            %(relative_humidity_2m)s,
            %(wind_speed_10m)s,
            %(surface_pressure)s,
            %(weather_code)s
        );
    """

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(insert_sql, record)

        logger.info(
            f"Inserted record for {record['city']} "
            f"at {record['extraction_timestamp']}"
        )

    except Exception as e:
        logger.error(f"Failed to insert record: {e}")
        raise