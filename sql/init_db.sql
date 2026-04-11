-- sql/init_db.sql
-- Runs automatically on first PostgreSQL container startup.
-- Creates the weather_db database alongside the Airflow metadata database.

-- PostgreSQL does not support CREATE DATABASE inside a transaction,
-- so we use a DO block to check existence first.

SELECT 'CREATE DATABASE weather_db'
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'weather_db'
)\gexec

-- Grant the airflow user full access to weather_db
GRANT ALL PRIVILEGES ON DATABASE weather_db TO airflow;
