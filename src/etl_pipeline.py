"""
src/etl_pipeline.py

Orchestrates the full ETL: extract -> transform -> load
Provides a CLI to run the end-to-end process locally.

Usage example:
  python src/etl_pipeline.py --search "data scientist" --limit 200

Outputs:
  - data/raw/remotive_jobs.json
  - data/processed/jobs_clean.csv
  - data/jobs.db (if using sqlite)
"""
from __future__ import annotations
import argparse
import os
from src import extractor, transformer, loader


def run_etl(search: str | None, category: str | None, limit: int | None, db_url: str = "sqlite:///data/jobs.db"):
    raw_dir = "data/raw"
    processed_dir = "data/processed"
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)

    raw_path = os.path.join(raw_dir, "remotive_jobs.json")
    processed_path = os.path.join(processed_dir, "jobs_clean.csv")

    # Extract
    raw = extractor.fetch_remotive_jobs(search=search, category=category, limit=limit)
    records = extractor.parse_jobs(raw)
    extractor.save_jobs_to_json(records, raw_path)

    # Transform
    recs = transformer.transform_records(records)
    transformer.save_df(recs, processed_path)

    # Load (init schema and load)
    loader.init_db_from_schema(loader.get_engine(db_url), schema_sql_path="database/schema.sql")
    loader.load_csv_to_db(processed_path, db_url)

    print("ETL completed: raw saved to", raw_path, "clean saved to", processed_path)


def cli():
    parser = argparse.ArgumentParser(description="Run ETL pipeline")
    parser.add_argument("--search", help="Search query (e.g., 'data scientist')", default=None)
    parser.add_argument("--category", help="Category filter", default=None)
    parser.add_argument("--limit", help="Max jobs to fetch (int)", type=int, default=200)
    parser.add_argument("--db", help="DB URL", default="sqlite:///data/jobs.db")
    args = parser.parse_args()
    run_etl(args.search, args.category, args.limit, db_url=args.db)


if __name__ == "__main__":
    cli()
