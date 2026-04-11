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
