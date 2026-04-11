from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

# Default arguments applied to every task in this DAG 
default_args = {
    "owner":            "student",
    "depends_on_past":  False,
    "email_on_failure": False,
    "email_on_retry":   False,
    "retries":          1,
    "retry_delay":      timedelta(minutes=5),
}

# DAG definition 
with DAG(
    dag_id="daily_weather_pipeline",
    description="Extracts daily weather for Colombo and stores it in PostgreSQL",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule="@daily",   # 'schedule' replaces the deprecated 'schedule_interval'
    catchup=False,       # do not run historical dates on first start
    tags=["weather", "coursework"],
) as dag:

    # Task: extract and store weather data
    extract_and_store = BashOperator(
        task_id="extract_and_store_weather",
        bash_command="cd /opt/airflow && python -m scripts.extract_and_store_weather",
        # Set environment variables for the task. These will override any existing variables in the container.
        env={
            "PYTHONPATH":        "/opt/airflow",
            "POSTGRES_HOST":     "postgres",
            "POSTGRES_PORT":     "5432",
            "POSTGRES_USER":     "airflow",
            "POSTGRES_PASSWORD": "airflow",
            "WEATHER_DB":        "weather_db",
            "LATITUDE":          "6.9271",
            "LONGITUDE":         "79.8612",
            "CITY_NAME":         "Colombo",
        },
        append_env=True,  # keep the container's existing PATH etc.
    )

    # Only one task — nothing to chain
    extract_and_store
