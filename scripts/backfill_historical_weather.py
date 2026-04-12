import argparse
import logging
import sys
from datetime import date, datetime, timedelta
 
import psycopg2
import requests
 
# Relative imports 
from .config import (
    CITY_NAME,
    DB_CONFIG,
    LATITUDE,
    LONGITUDE,
    WEATHER_VARIABLES,
)
 
# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
 
# Constants
HISTORICAL_API_URL = "https://archive-api.open-meteo.com/v1/archive"
 
# Default number of past days to fetch 
DEFAULT_DAYS = 30
 
 
# API 
 
def fetch_historical_weather(start_date: date, end_date: date) -> dict:
    """
    Fetch historical hourly weather data for the specified date range.
        Uses the Open-Meteo "archive" API endpoint, which provides historical
        data back to 1979.
    
        Parameters
        ----------
        start_date : date object
        end_date   : date object 
    
        Returns
        -------
        dict: the raw JSON response from the API, parsed into a Python dict.
    """
    params = {
        "latitude":   LATITUDE,
        "longitude":  LONGITUDE,
        "start_date": start_date.isoformat(),   
        "end_date":   end_date.isoformat(),    
        "hourly":     ",".join(WEATHER_VARIABLES),
        "timezone":   "Asia/Colombo",
    }
 
    logger.info(
        f"Fetching historical data for {CITY_NAME} "
        f"from {start_date} to {end_date} "
        f"({(end_date - start_date).days + 1} days)"
    )
 
    response = requests.get(HISTORICAL_API_URL, params=params, timeout=30)
    response.raise_for_status()
 
    data = response.json()
 
    # Validate that the response has the structure we expect
    if "hourly" not in data:
        raise ValueError("API response is missing the 'hourly' key.")
    if "time" not in data["hourly"]:
        raise ValueError("API response 'hourly' block is missing 'time'.")
 
    missing_vars = [v for v in WEATHER_VARIABLES if v not in data["hourly"]]
    if missing_vars:
        raise ValueError(f"API response is missing variables: {missing_vars}")
 
    logger.info(
        f"Received {len(data['hourly']['time'])} hourly records from API."
    )
    return data
 
 
# Parsing
 
def parse_historical_records(data: dict) -> list[dict]:
    """
    Convert the raw API response into a list of row dicts ready for insertion.
 
    The API returns data as parallel arrays:
        hourly["time"]             = ["2026-03-01T00:00", "2026-03-01T01:00", ...]
        hourly["temperature_2m"]   = [28.1, 27.9, ...]
        hourly["weather_code"]     = [0, 1, ...]
        ...
 
    We zip them together into one dict per hour.
 
    Record dict schema matches the weather_data table:
    {
        "extraction_timestamp": datetime,
        "city":                 str,
        "temperature_2m":       float,
        "relative_humidity_2m": float,
        "wind_speed_10m":       float,
        "surface_pressure":     float,
        "weather_code":         int
    }
 
    Returns
    -------
    list of dicts, each matching the weather_data table schema.
    """
    hourly  = data["hourly"]
    times   = hourly["time"]
    records = []
    skipped = 0
 
    for i, timestamp_str in enumerate(times):
        temp     = hourly["temperature_2m"][i]
        humidity = hourly["relative_humidity_2m"][i]
        wind     = hourly["wind_speed_10m"][i]
        pressure = hourly["surface_pressure"][i]
        code     = hourly["weather_code"][i]
 
        # Skip rows where all weather values are None (gaps in historical data)
        if all(v is None for v in [temp, humidity, wind, pressure, code]):
            skipped += 1
            continue
 
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M")
 
        records.append({
            "extraction_timestamp": timestamp,
            "city":                 CITY_NAME,
            "temperature_2m":       temp,
            "relative_humidity_2m": humidity,
            "wind_speed_10m":       wind,
            "surface_pressure":     pressure,
            "weather_code":         int(code) if code is not None else None,
        })
 
    if skipped:
        logger.warning(f"Skipped {skipped} fully-empty rows from API response.")
 
    logger.info(f"Parsed {len(records)} valid records ready for insertion.")
    return records
 
 
# Database 
 
def get_existing_timestamps(conn) -> set:
    """
    Return the set of (city, extraction_timestamp) pairs already in the table.
 
    Used to skip duplicate inserts — if you run this script twice, it will
    not insert the same hourly record a second time.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT city, extraction_timestamp FROM weather_data;"
        )
        return set(cur.fetchall())
 
 
def bulk_insert(records: list[dict], skip_duplicates: bool = True) -> tuple[int, int]:
    """
    Insert all records into weather_data in a single database transaction.
 
    Using one transaction for all rows is much faster than opening and
    closing a connection for each row (which is what insert_weather() in
    db_utils.py does — fine for one row per day, slow for 720 rows at once).
 
    Parameters
    ----------
    records         : list of dicts produced by parse_historical_records()
    skip_duplicates : if True, check existing timestamps and skip matches
 
    Returns
    -------
    (inserted_count, skipped_count)
    """
    if not records:
        logger.warning("No records to insert.")
        return 0, 0
 
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
    inserted = 0
    skipped  = 0
 
    try:
        conn = psycopg2.connect(**DB_CONFIG)
 
        # Load existing timestamps once — much faster than querying per row
        existing = get_existing_timestamps(conn) if skip_duplicates else set()
        if existing:
            logger.info(
                f"Found {len(existing)} existing records in DB — "
                f"duplicates will be skipped."
            )
 
        with conn.cursor() as cur:
            for record in records:
                key = (record["city"], record["extraction_timestamp"])
 
                if skip_duplicates and key in existing:
                    skipped += 1
                    continue
 
                cur.execute(insert_sql, record)
                inserted += 1
 
        conn.commit()
        logger.info(f"Transaction committed — {inserted} rows inserted.")
 
    except psycopg2.OperationalError as e:
        logger.error(
            f"Could not connect to PostgreSQL: {e}\n"
            f"Check that the Docker containers are running and that\n"
            f"POSTGRES_HOST in your .env file is set to 'localhost'."
        )
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Insert failed — transaction rolled back: {e}")
        raise
    finally:
        if conn:
            conn.close()
 
    return inserted, skipped
 
 
# Entry point 
 
def main():
    parser = argparse.ArgumentParser(
        description="Back-fill historical weather data into weather_data table."
    )
    parser.add_argument(
        "--days",
        type=int,
        default=DEFAULT_DAYS,
        help=f"Number of past days to fetch (default: {DEFAULT_DAYS})",
    )
    args = parser.parse_args()
 
    if args.days < 1 or args.days > 365:
        logger.error("--days must be between 1 and 365.")
        sys.exit(1)
 
    # Calculate date range.
    end_date   = date.today()
    start_date = end_date - timedelta(days=args.days - 1)
 
    logger.info(f"Back-fill range: {start_date}  →  {end_date}  ({args.days} days)")
 
    try:
        # Step 1 — Fetch from API
        raw_data = fetch_historical_weather(start_date, end_date)
 
        # Step 2 — Parse into row dicts
        records = parse_historical_records(raw_data)
 
        if not records:
            logger.warning("No valid records returned from API. Nothing to insert.")
            sys.exit(0)
 
        # Step 3 — Insert into PostgreSQL (with duplicate protection)
        inserted, skipped = bulk_insert(records, skip_duplicates=True)
 
        # Step 4 — Summary
        logger.info("=" * 55)
        logger.info(f"  Back-fill complete.")
        logger.info(f"  Date range : {start_date} → {end_date}")
        logger.info(f"  Inserted   : {inserted} rows")
        logger.info(f"  Skipped    : {skipped} duplicates")
        logger.info(f"  Total API  : {len(records)} valid records")
        logger.info("=" * 55)
 
    except requests.exceptions.Timeout:
        logger.error("API request timed out. Check your internet connection.")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        logger.error(f"API HTTP error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"API response parsing error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
 
 
if __name__ == "__main__":
    main()