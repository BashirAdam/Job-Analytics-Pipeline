"""
src/loader.py

Load cleaned CSV into a relational database (SQLite by default, Postgres optional).
Uses SQLAlchemy for DB connections. If table does not exist, will create it.

Usage examples:
  python src/loader.py --csv data/processed/jobs_clean.csv --db sqlite:///data/jobs.db --table jobs

Dependencies:
  pip install sqlalchemy pandas psycopg2-binary
"""
from __future__ import annotations
import argparse
import os
import sqlalchemy
import pandas as pd
from sqlalchemy import text


def get_engine(db_url: str):
    """Return a SQLAlchemy engine for given DB URL."""
    return sqlalchemy.create_engine(db_url)


def init_db_from_schema(engine, schema_sql_path: str | None = None):
    """Initialize DB using schema.sql if provided."""
    if schema_sql_path and os.path.exists(schema_sql_path):
        with open(schema_sql_path, "r", encoding="utf-8") as f:
            schema = f.read()
        with engine.begin() as conn:
            conn.execute(text(schema))


def load_csv_to_db(csv_path: str, db_url: str, table_name: str = "jobs", if_exists: str = "append") -> None:
    """Load a CSV file into database table using pandas.to_sql.

    Args:
        csv_path: path to cleaned CSV
        db_url: SQLAlchemy DB URL
        table_name: destination table name
        if_exists: pandas to_sql if_exists behavior ('append' or 'replace')
    """
    df = pd.read_csv(csv_path)
    engine = get_engine(db_url)
    # Ensure DB file path exists for sqlite
    if db_url.startswith("sqlite:"):
        db_dir = os.path.dirname(db_url.replace("sqlite://", ""))
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    # Use to_sql for portable loading
    df.to_sql(table_name, con=engine, if_exists=if_exists, index=False, method="multi")
    print(f"Loaded {len(df)} rows into {table_name} at {db_url}")


def cli():
    parser = argparse.ArgumentParser(description="Load cleaned CSV into DB")
    parser.add_argument("--csv", required=True, help="Path to cleaned CSV (from transformer)")
    parser.add_argument("--db", required=False, default="sqlite:///data/jobs.db", help="SQLAlchemy DB URL")
    parser.add_argument("--table", required=False, default="jobs", help="Destination table name")
    parser.add_argument("--schema", required=False, default="database/schema.sql", help="Optional SQL schema file to run before loading")
    args = parser.parse_args()
    engine = get_engine(args.db)
    init_db_from_schema(engine, args.schema)
    load_csv_to_db(args.csv, args.db, args.table)


if __name__ == "__main__":
    cli()
