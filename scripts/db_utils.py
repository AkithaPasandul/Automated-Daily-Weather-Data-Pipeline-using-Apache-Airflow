"""
db_utils.py — Reusable database helper functions.

Provides three clean functions:
  - get_connection()   : opens a psycopg2 connection to PostgreSQL
  - create_table()     : creates the weather_data table if it does not exist
  - insert_weather()   : inserts a single weather record into the table
"""

import logging
import psycopg2
from scripts.config import DB_CONFIG

logger = logging.getLogger(__name__)


def get_connection():
    """
    Return a live psycopg2 connection using settings from config.py.
    Raises an exception if the connection fails.
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
    """
    Create the weather_data table if it does not already exist.
    Safe to call every time the pipeline runs.
    """
    create_sql = """
        CREATE TABLE IF NOT EXISTS weather_data (
            id                    SERIAL PRIMARY KEY,
            extraction_timestamp  TIMESTAMP NOT NULL,
            city                  VARCHAR(100) NOT NULL,
            temperature_2m        FLOAT,
            relative_humidity_2m  FLOAT,
            wind_speed_10m        FLOAT,
            surface_pressure      FLOAT,
            weather_code          INT
        );
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(create_sql)
        conn.commit()
        logger.info("Table 'weather_data' is ready.")
    except Exception as e:
        logger.error(f"Failed to create table: {e}")
        raise
    finally:
        if conn:
            conn.close()


def insert_weather(record: dict):
    """
    Insert one row into the weather_data table.

    Parameters
    ----------
    record : dict
        Must contain these keys:
        extraction_timestamp, city, temperature_2m,
        relative_humidity_2m, wind_speed_10m,
        surface_pressure, weather_code
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
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(insert_sql, record)
        conn.commit()
        logger.info(f"Inserted weather record for {record['city']} at {record['extraction_timestamp']}")
    except Exception as e:
        logger.error(f"Failed to insert record: {e}")
        raise
    finally:
        if conn:
            conn.close()
