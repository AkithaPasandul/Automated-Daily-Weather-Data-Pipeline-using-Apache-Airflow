# Weather Airflow Pipeline

A local automated weather data pipeline built with Apache Airflow, Docker Compose, PostgreSQL, and Jupyter Notebook.

**Course:** Data Science Undergraduate — Automated Data Pipeline Coursework  
**Data source:** [Open-Meteo API](https://open-meteo.com/) (free, no API key required)  
**Location:** Colombo, Sri Lanka

---

## Project Purpose

This pipeline automatically fetches current weather conditions for Colombo once per day, stores the records in a PostgreSQL database, and visualises trends in a Jupyter Notebook. The entire stack runs locally inside Docker containers.

---

## Project Structure

```
weather-airflow-pipeline/
│
├── dags/
│   └── weather_pipeline_dag.py      ← Airflow DAG (daily schedule)
│
├── scripts/
│   ├── __init__.py
│   ├── config.py                    ← Reads env vars for DB + API settings
│   ├── db_utils.py                  ← DB connection, table creation, insert
│   └── extract_and_store_weather.py ← Main ETL script
│
├── notebooks/
│   └── weather_visualization.ipynb  ← Charts and analysis
│
├── sql/
│   ├── create_weather_table.sql     ← Table DDL (reference)
│   └── init_db.sql                  ← Creates weather_db on first startup
│
├── screenshots/                     ← Put your report screenshots here
├── report/                          ← Put your written report here
│
├── requirements.txt
├── docker-compose.yaml
├── .env.example
└── README.md
```

---

## Prerequisites

| Tool | Version |
|------|---------|
| Docker Desktop | Latest (Windows, WSL2 backend) |
| Python | 3.11+ (for running notebook on host) |
| Git | Any |

---

## Setup Steps

### 1. Clone or download the project

```bash
git clone <your-repo-url>
cd weather-airflow-pipeline
```

### 2. Create the .env file

```bash
# Windows Command Prompt:
copy .env.example .env

# Windows PowerShell or Git Bash:
cp .env.example .env
```

You can leave all defaults — no API key is needed.

### 3. Create required directories

```bash
mkdir logs plugins
```

> Airflow requires a `logs/` and `plugins/` folder to start.

### 4. Start all Docker services

```bash
docker compose up airflow-init
```

Wait for the init container to finish (you will see `admin user created`), then:

```bash
docker compose up -d airflow-webserver airflow-scheduler postgres
```

### 5. Verify containers are running

```bash
docker compose ps
```

All three services (`weather_postgres`, `airflow_webserver`, `airflow_scheduler`) should show **running**.

---

## Accessing Airflow

Open your browser and go to:

```
http://localhost:8080
```

**Username:** `admin`  
**Password:** `admin`

---

## Triggering the DAG

1. Open the Airflow UI at `http://localhost:8080`
2. Find the DAG named **`daily_weather_pipeline`**
3. Toggle it **On** using the switch on the left
4. Click the **▶ Play** button to trigger a manual run immediately
5. Click the DAG name → **Graph** view to watch the task progress
6. Click the task box → **Logs** to see extraction output

---

## Running the Jupyter Notebook

Install dependencies on your host machine (outside Docker):

```bash
pip install -r requirements.txt
```

Start Jupyter:

```bash
cd notebooks
jupyter notebook
```

Open `weather_visualization.ipynb` and run all cells.

> The notebook connects to `localhost:5432` — the PostgreSQL port exposed by Docker.

---

## Manual Script Test (optional)

To test the extraction script outside Airflow:

```bash
# From the project root
pip install -r requirements.txt
python -m scripts.extract_and_store_weather
```

You should see log lines confirming a successful insert.

---

## How the Files Work Together

```
docker-compose.yaml
   └── starts postgres, airflow-webserver, airflow-scheduler

Airflow Scheduler
   └── reads dags/weather_pipeline_dag.py
         └── daily schedule triggers BashOperator
               └── runs: python -m scripts.extract_and_store_weather
                     ├── scripts/config.py    (reads env vars)
                     ├── scripts/db_utils.py  (PostgreSQL helpers)
                     └── calls Open-Meteo API → inserts row → logs result

Jupyter Notebook
   └── connects to postgres → reads weather_data → draws charts
```

---

## Common Setup Issues

| Problem | Fix |
|---------|-----|
| `airflow_webserver` not starting | Wait 60 seconds after init. Check `docker compose logs airflow-webserver` |
| DAG not appearing in UI | Wait 30 seconds for the scheduler to pick it up. Check `docker compose logs airflow-scheduler` |
| `weather_db` not found | The `sql/init_db.sql` script creates it on first Postgres start. Delete the `postgres_data` volume and restart: `docker compose down -v && docker compose up -d` |
| Notebook can't connect | Ensure `localhost:5432` is reachable. Run `docker compose ps` to confirm postgres is healthy |
| `ModuleNotFoundError: scripts` | Run the script from the project root: `python -m scripts.extract_and_store_weather` |

---

## What Screenshots the Student Should Capture

Capture these screenshots for your coursework report:

1. **`docker_containers_running.png`**  
   `docker compose ps` output in terminal showing all three services as running/healthy.

2. **`airflow_ui_login.png`**  
   The Airflow login screen at `http://localhost:8080`.

3. **`airflow_dag_list.png`**  
   The DAGs list page showing `daily_weather_pipeline` toggled On.

4. **`airflow_dag_graph.png`**  
   The Graph view of a successful DAG run with the task shown in green.

5. **`airflow_task_logs.png`**  
   Task log output showing the API call, parsed values, and successful insert message.

6. **`postgres_table_data.png`**  
   A query result showing rows in the `weather_data` table. Use any PostgreSQL client (pgAdmin, DBeaver, or `docker exec -it weather_postgres psql -U airflow -d weather_db -c "SELECT * FROM weather_data LIMIT 10;"`).

7. **`jupyter_notebook_running.png`**  
   The notebook open in the browser with all cells executed.

8. **`chart_temperature.png`**  
   Temperature over time chart (auto-saved by the notebook).

9. **`chart_wind_speed.png`**  
   Wind speed over time chart (auto-saved by the notebook).

10. **`project_folder_structure.png`**  
    Your file explorer or `tree` command showing the project layout.
