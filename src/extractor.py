"""
src/extractor.py

Fetch job postings from Remotive public API:
https://remotive.io/api/remote-jobs

Provides:
- fetch_remotive_jobs: Retrieve raw JSON (with retries)
- parse_jobs: Normalize & clean job records
- save_jobs_to_json / save_jobs_to_csv
- CLI to run and save results

Usage (example):
  python src/extractor.py --search "data scientist" --limit 100 --output data/raw/jobs.json --format json
"""

from __future__ import annotations
import argparse
import json
import logging
import os
from typing import Dict, List, Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Public API endpoint
REMOTIVE_API_URL = "https://remotive.io/api/remote-jobs"

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("extractor")


def requests_session_with_retries(
    total_retries: int = 3, backoff_factor: float = 0.3, status_forcelist=(429, 500, 502, 503, 504)
) -> requests.Session:
    """
    Return a requests.Session configured with retries.
    """
    session = requests.Session()
    retries = Retry(
        total=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=("GET",),
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({"User-Agent": "job-analytics-pipeline/1.0 (+https://github.com/)"})
    return session


def fetch_remotive_jobs(search: Optional[str] = None, category: Optional[str] = None, limit: Optional[int] = None) -> Dict:
    """
    Fetch jobs from Remotive API.

    Args:
        search: text to search in Remotive (query param 'search')
        category: job category (query param 'category')
        limit: maximum number of jobs to return (None = all)

    Returns:
        Raw JSON (parsed into dict)
    """
    session = requests_session_with_retries()
    params = {}
    if search:
        params["search"] = search
    if category:
        params["category"] = category

    logger.info("Fetching jobs from Remotive API with params=%s", params)
    resp = session.get(REMOTIVE_API_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    # Remotive returns {"jobs": [...]} — optionally trim to `limit`
    if limit is not None and isinstance(limit, int):
        data["jobs"] = data.get("jobs", [])[:limit]

    logger.info("Fetched %d jobs", len(data.get("jobs", [])))
    return data


def html_to_text(html: Optional[str]) -> str:
    """
    Convert HTML snippet to plain text safely.
    """
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n").strip()


def parse_jobs(raw: Dict) -> List[Dict]:
    """
    Normalize Remotive job JSON into flat records.

    Keeps fields:
      - id, url, title, company_name, category, job_type,
        publication_date, candidate_required_location, salary,
        description_text, tags (list => comma string)
    """
    jobs = raw.get("jobs", [])
    records = []
    for j in jobs:
        rec = {
            "id": j.get("id"),
            "url": j.get("url"),
            "title": j.get("title"),
            "company_name": j.get("company_name"),
            "category": j.get("category"),
            "job_type": j.get("job_type"),
            "publication_date": j.get("publication_date"),
            "candidate_required_location": j.get("candidate_required_location"),
            "salary": j.get("salary"),
            "description_text": html_to_text(j.get("description")),
            "tags": ", ".join(j.get("tags", [])) if j.get("tags") else "",
            "raw": j,  # keep raw for debugging/extra fields
        }
        records.append(rec)
    return records


def save_jobs_to_json(records: List[Dict], path: str) -> None:
    """
    Save parsed job list to a JSON file (pretty).
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    logger.info("Saved %d records to %s", len(records), path)


def save_jobs_to_csv(records: List[Dict], path: str) -> None:
    """
    Save parsed job list to a CSV file using pandas.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df = pd.DataFrame(records)
    # Drop the raw large JSON column for CSV brevity if present
    if "raw" in df.columns:
        df = df.drop(columns=["raw"])
    df.to_csv(path, index=False)
    logger.info("Saved %d records to %s", len(df), path)


def run_and_save(search: Optional[str], category: Optional[str], limit: Optional[int], out_path: str, fmt: str) -> None:
    raw = fetch_remotive_jobs(search=search, category=category, limit=limit)
    records = parse_jobs(raw)
    if fmt == "json":
        save_jobs_to_json(records, out_path)
    elif fmt == "csv":
        save_jobs_to_csv(records, out_path)
    else:
        raise ValueError("Unsupported format: choose 'json' or 'csv'")

    # Print brief summary
    logger.info("Example record (first): %s", records[0] if records else "No records")


def cli():
    parser = argparse.ArgumentParser(description="Extract job data from Remotive (public API)")
    parser.add_argument("--search", help="Search query (e.g., 'data scientist')", default=None)
    parser.add_argument("--category", help="Category filter", default=None)
    parser.add_argument("--limit", help="Max jobs to fetch (int)", type=int, default=None)
    parser.add_argument("--output", help="Output path", default="data/raw/remotive_jobs.json")
    parser.add_argument("--format", help="Output format: json or csv", choices=["json", "csv"], default="json")
    args = parser.parse_args()
    run_and_save(args.search, args.category, args.limit, args.output, args.format)


if __name__ == "__main__":
    cli()
