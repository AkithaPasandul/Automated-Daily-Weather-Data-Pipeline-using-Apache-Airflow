# Weather Airflow Pipeline

A local automated weather data pipeline built with Apache Airflow, Docker Compose,
PostgreSQL and Jupyter Notebook.

**Course:** Data Science Undergraduate — Automated Data Pipeline Coursework  
**Data source:** [Open-Meteo API](https://open-meteo.com/)  
**Location:** Colombo, Sri Lanka

---

## Project Structure

```
weather-airflow-pipeline/
│
├── dags/
│   └── weather_pipeline_dag.py              ← Airflow DAG (daily schedule)
│
├── scripts/
│   ├── __init__.py                          ← Makes 'scripts' a Python package
│   ├── config.py                            ← All settings read from environment variables
│   ├── db_utils.py                          ← get_connection(), create_table(), insert_weather()
│   ├── extract_and_store_weather.py         ← Main ETL: API → parse → PostgreSQL
│   └── backfill_historical_weather.py       ← One-off script: loads 30 days of history
│
├── notebooks/
│   └── weather_visualization.ipynb          ← Connects to DB and draws charts
│
├── sql/
│   ├── init_db.sh                           ← Creates weather_db on first Postgres startup
│   ├── init_db.sql                          ← Creates weather_data table inside weather_db
│   └── create_weather_table.sql             ← Reference DDL (informational only)
│
├── config/                                  ← Empty folder required by Airflow
├── logs/                                    ← Airflow writes task logs here (git-ignored)
├── plugins/                                 ← Empty folder required by Airflow
│
├── requirements.txt
├── docker-compose.yaml
├── .gitignore
└── README.md
```

---

## Prerequisites

| Tool | Notes |
|------|-------|
| Docker Desktop | Enable WSL2 backend on Windows. Allocate at least 4 GB RAM in Docker settings. |
| Python 3.11+ | Only needed on your host machine for running Jupyter Notebook. |

---

## Exact Run Order

Follow these steps **in order**. Do not skip any step.

### Step 1 — Copy the environment file

```bash
# Windows Command Prompt:
copy .env.example .env

# PowerShell:
Copy-Item .env.example .env

# Git Bash / WSL / macOS:
cp .env.example .env
```

No values need to be changed for a basic local setup.

### Step 2 — Create all required local directories

Airflow and Docker expect these folders to exist before the containers start.

```bash
# Windows Command Prompt — run each line separately:
mkdir logs
mkdir plugins
mkdir config
mkdir screenshots

# Git Bash / WSL / macOS:
mkdir -p logs plugins config screenshots
```

### Step 3 — Make the database init script executable (Git Bash / WSL only)

```bash
chmod +x sql/init_db.sh
```

> Windows Command Prompt and PowerShell users can skip this step — Docker handles permissions automatically.

### Step 4 — Start PostgreSQL and wait for it to be healthy

```bash
docker compose up -d postgres
```

Wait about 15 seconds, then check:

```bash
docker compose ps
```

The `STATUS` for `weather_postgres` must say **healthy** before you continue.  
If it says `starting`, wait a few more seconds and run `docker compose ps` again.

### Step 5 — Run the one-time Airflow initialisation

```bash
docker compose up airflow-init
```

Run this in the **foreground** so you can watch the output. The container runs database migrations, creates the admin user, then prints the Airflow version number (e.g. `2.8.1`) and exits automatically with code 0. **This is expected and correct.**

### Step 6 — Start the webserver and scheduler

```bash
docker compose up -d airflow-webserver airflow-scheduler
```

### Step 7 — Verify all containers

```bash
docker compose ps
```

You should see four containers. The exact name prefix depends on your folder name, but the statuses should match:

| Container | Status |
|-----------|--------|
| `weather_postgres` | `healthy` |
| `...-airflow-init-1` | `exited (0)` — correct, this is expected |
| `...-airflow-webserver-1` | `running` |
| `...-airflow-scheduler-1` | `running` |

> The `...` prefix is your project folder name (e.g. `weather-airflow-pipeline`). Only `weather_postgres` has a fixed name because it is set explicitly in `docker-compose.yaml`.

### Step 8 — Open the Airflow UI

Wait 30–60 seconds after Step 6, then open: **http://localhost:8080**

- Username: `admin`
- Password: `admin`

### Step 9 — Trigger the DAG manually

1. Find **`daily_weather_pipeline`** in the DAGs list.
2. Toggle the **On/Off switch** on the left to **On**.
3. Click the **▶ Trigger DAG** button (play icon on the right side of the row).
4. Click the DAG name to open it, then select the **Graph** tab.
5. When the task box turns **green**, the run succeeded.
6. Click the task box → **Logs** to see the full extraction output.

### Step 10 — Verify data in PostgreSQL

```bash
docker exec -it weather_postgres psql -U airflow -d weather_db -c "SELECT * FROM weather_data;"
```

You should see one row per successful DAG run.

### Step 11 — Back-fill 30 days of historical data (recommended)

The DAG inserts one record per day. To get enough data for meaningful charts,
run the back-fill script once to load 30 days of hourly historical data (~720 rows):

```bash
# Make sure your .env has POSTGRES_HOST=localhost, then run from the project root:
python -m scripts.backfill_historical_weather
```

To choose a different number of days (between 1 and 365):

```bash
python -m scripts.backfill_historical_weather --days 14
```

The script is safe to run multiple times — it skips any timestamps already in the database.

### Step 12 — Run the Jupyter Notebook

Install dependencies on your **host machine** (not inside Docker):

```bash
pip install -r requirements.txt
```

Launch Jupyter from the **project root**:

```bash
jupyter notebook
```

Open `notebooks/weather_visualization.ipynb` and run all cells with **Cell → Run All**.

Charts are saved automatically to the `screenshots/` folder.

---

## Testing the ETL Script Manually

You can run the main extraction script directly on your host machine to verify it works before Airflow runs it. Make sure your `.env` file has `POSTGRES_HOST=localhost` (not `postgres`).

```bash
# From the project root:
python -m scripts.extract_and_store_weather
```

---

## How the Files Work Together

```
docker-compose.yaml
  ├── postgres
  │     └── runs sql/init_db.sh on first startup
  │           └── creates weather_db
  │                 └── runs sql/init_db.sql → creates weather_data table
  ├── airflow-init  → migrates Airflow DB, creates admin user, then exits
  ├── airflow-webserver → serves UI at http://localhost:8080
  └── airflow-scheduler
        └── reads dags/weather_pipeline_dag.py
              └── @daily BashOperator →
                    python -m scripts.extract_and_store_weather
                      ├── scripts/config.py     (reads env vars)
                      ├── scripts/db_utils.py   (DB helpers)
                      └── Open-Meteo API → parse → INSERT into weather_data

scripts/backfill_historical_weather.py  (run once manually)
  └── Open-Meteo Historical API → 30 days × 24 hours → bulk INSERT into weather_data

notebooks/weather_visualization.ipynb
  └── SQLAlchemy → localhost:5432/weather_db
      └── reads weather_data → matplotlib charts → saves PNGs to screenshots/
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `weather_postgres` stuck on `starting` | Run `docker compose logs postgres`. If it shows "database system is ready", just wait another 10 s. |
| `airflow-init` exits with non-zero code | Run `docker compose logs airflow-init`. Usually a permissions or DB connection issue. Try `docker compose down -v` then repeat from Step 4. |
| Webserver not reachable at :8080 | It takes 30–60 s to start after Step 6. Run `docker compose logs airflow-webserver` to watch progress. |
| DAG not visible in UI | Wait 30 s for the scheduler to scan. Check `docker compose logs airflow-scheduler` for import errors. |
| Task fails: `ModuleNotFoundError: scripts` | The `PYTHONPATH=/opt/airflow` env var in both `docker-compose.yaml` and the DAG's `env` dict fixes this. Confirm `./scripts` is listed in the volumes section. |
| `weather_db does not exist` | `init_db.sh` only runs on the very first Postgres startup. If you started postgres before the `sql/` files existed, tear down the volume and restart: `docker compose down -v` then repeat from Step 4. |
| Notebook: `connection refused` on port 5432 | Confirm Docker is running (`docker compose ps`). Confirm you are using `localhost`, not `postgres`, in the DB URL. |
| Notebook: `FileNotFoundError: screenshots/` | Run `mkdir screenshots` from the project root, then re-run the notebook cell. |
| Manual script: `could not connect to server` | Confirm `.env` has `POSTGRES_HOST=localhost` (not `postgres`). `postgres` only resolves inside Docker's internal network. |
| Backfill script: `connection refused` | Same as above — Docker containers must be running and `.env` must have `POSTGRES_HOST=localhost`. |

---