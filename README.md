# Job Market Analytics Pipeline & Dashboard 

Professional end-to-end portfolio project showing an ETL pipeline that extracts job postings, cleans and stores them, and exposes a deployed interactive dashboard.

---

## Project Overview

**Goal:** Build a data pipeline that extracts real job postings, transforms and stores them in a database, and visualizes insights via an interactive dashboard.

**Tech stack:** Python (requests, pandas, BeautifulSoup), Streamlit, SQLAlchemy, SQLite/Postgres, Docker, GitHub Actions.


## Project Structure

```
job-analytics-pipeline/
├── src/
│   ├── extractor.py          # Data extraction from Remotive API
│   ├── transformer.py        # Data cleaning & transformation
│   ├── loader.py             # Load to DB (SQLite/Postgres)
│   └── etl_pipeline.py       # Main ETL orchestration
├── database/
│   ├── schema.sql            # Database schema
│   └── queries.sql           # Analytical queries
├── dashboard/
│   ├── app.py                # Streamlit app
│   └── components/           # UI helpers
├── tests/
│   └── test_etl.py           # Unit tests
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── .github/
│   └── workflows/ci.yml      # CI pipeline
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Quickstart — Local (recommended)

1. Create a virtual environment and install dependencies

```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell
pip install -r requirements.txt
```

2. Run the ETL (extract -> transform -> load)

```bash
python src/etl_pipeline.py --search "data scientist" --limit 200
```

Outputs:
- `data/raw/remotive_jobs.json`
- `data/processed/jobs_clean.csv`
- `data/jobs.db` (SQLite DB)

3. Start dashboard

```bash
streamlit run dashboard/app.py
# Open http://localhost:8501
```

---

## Quickstart — Docker

Build and run with Docker Compose:

```bash
docker-compose up --build
# App available at http://localhost:8501
```

---

## Deploying (Free Hosting options)

- Streamlit Community Cloud: Push repo to GitHub, create a new app in Streamlit Cloud pointing to `dashboard/app.py`. Ensure `requirements.txt` is present.
- Render / Railway: Build Docker image with provided `docker/Dockerfile` and deploy.


## CI

GitHub Actions workflow runs `pytest` on push/pull requests to `main` branch — see `.github/workflows/ci.yml`.

---

## Database schema & Analytics

- Initialize DB: `sqlite:///data/jobs.db` is used by default. Schema at `database/schema.sql`.
- Pre-written queries in `database/queries.sql` for quick analysis (top skills, salary stats, etc.).

---

## Running tests

```bash
pytest -q
```

---

## Screenshots

> **Add screenshots here** after you run the dashboard. Example placeholders:
>
> - `docs/screenshots/dashboard_kpis.png`
> - `docs/screenshots/top_skills.png`

---

## Notes

- The extractor uses the public Remotive API (no key) — it's ethical to use for this demo.
- For production, add rate-limiting, job deduplication policies, and robust monitoring.

---

## Next improvements (ideas)

- Normalize skills into a separate table for better analytics
- Add incremental runs and Airflow / Prefect orchestration
- Add authentication and multi-user dashboards

---





