#!/bin/bash
# sql/init_db.sh
#
# Executed automatically on the FIRST startup of the postgres container.
# Docker runs every file in /docker-entrypoint-initdb.d/ in alphabetical
# order. Because this file is a .sh script, Docker sources it so that the
# $POSTGRES_USER variable (set by docker-compose) is available here.
#
# Why a shell script instead of plain SQL?
# CREATE DATABASE cannot run inside a transaction block.
# docker-entrypoint-initdb.d .sql files are wrapped in a transaction, so
# CREATE DATABASE inside a .sql file will always fail with:
#   "ERROR: CREATE DATABASE cannot run inside a transaction block"
# A .sh script sidesteps this by calling psql -c directly.
#
# Execution order (alphabetical):
#   1. init_db.sh  — creates weather_db database
#   2. init_db.sql — creates weather_data table inside weather_db

set -e   # abort immediately if any command returns a non-zero exit code

echo ">>> [init_db.sh] Checking whether weather_db exists..."

# Query pg_database; returns "1" if weather_db exists, empty string if not.
DB_EXISTS=$(psql -U "$POSTGRES_USER" -tAc \
    "SELECT 1 FROM pg_database WHERE datname = 'weather_db'")

if [ "$DB_EXISTS" = "1" ]; then
    echo ">>> [init_db.sh] weather_db already exists — skipping CREATE DATABASE."
else
    echo ">>> [init_db.sh] Creating database: weather_db"
    psql -U "$POSTGRES_USER" -c "CREATE DATABASE weather_db;"
    echo ">>> [init_db.sh] weather_db created successfully."
fi

echo ">>> [init_db.sh] Creating weather_data table inside weather_db..."
psql -U "$POSTGRES_USER" -d weather_db \
    -f /docker-entrypoint-initdb.d/init_db.sql

echo ">>> [init_db.sh] Initialisation complete."
