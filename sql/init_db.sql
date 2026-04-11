-- sql/init_db.sql
--
-- Called by init_db.sh after it creates the weather_db database.
-- This file runs inside weather_db (psql -d weather_db -f init_db.sql),
-- so it only needs to create the table — no CREATE DATABASE needed here.
--
-- IF NOT EXISTS makes this safe to run more than once.

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
