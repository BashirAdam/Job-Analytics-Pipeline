"""
src/transformer.py

Reads raw job records (JSON or CSV produced by extractor),
cleans and normalizes fields, extracts features (skills, seniority,
remote flag, salary ranges), deduplicates records, and writes
a cleaned CSV for loading to the database.

Usage examples:
  python src/transformer.py --input data/raw/remotive_jobs.json \
                           --output data/processed/jobs_clean.csv

Dependencies:
  pip install pandas python-dateutil
"""
from __future__ import annotations
import argparse
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
from dateutil import parser as date_parser

# Basic skill list (can extend or load from file)
COMMON_SKILLS = [
    "python", "sql", "aws", "docker", "kubernetes", "pandas", "spark",
    "tensorflow", "pytorch", "scikit-learn", "excel", "tableau",
    "powerbi", "java", "scala", "r", "javascript"
]

# Seniority keywords mapping
SENIORITY_MAP = {
    "senior": "senior",
    "sr.": "senior",
    "lead": "senior",
    "principal": "senior",
    "staff": "senior",
    "junior": "junior",
    "jr.": "junior",
    "intern": "intern",
    "manager": "manager",
}


def load_raw(path: str) -> List[Dict]:
    """
    Load raw records from JSON or CSV.
    Accepts list-of-dicts formatted JSON or an array of rows.
    """
    if path.lower().endswith(".json"):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # If the JSON contains the top-level dict with "jobs" key (from extractor)
        if isinstance(data, dict) and "jobs" in data:
            jobs = data["jobs"]
        else:
            jobs = data
        return jobs
    else:
        df = pd.read_csv(path)
        return df.to_dict(orient="records")


def clean_text(s: Optional[str]) -> str:
    """
    Basic whitespace and newline normalization, remove excessive spaces.
    """
    if not s:
        return ""
    s = re.sub(r"\r\n", "\n", s)
    s = re.sub(r"\n+", "\n", s)
    s = s.strip()
    return s


def parse_publication_date(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return date_parser.parse(s)
    except Exception:
        return None


def extract_skills(text: str, tags: str, extra_skills: Optional[List[str]] = None) -> List[str]:
    """
    Simple regex-based detection of skills from description + tags.
    """
    skills_set = set()
    text_lower = (text or "").lower()
    # include tags (comma-separated) as they often list skills
    tag_candidates = (tags or "")
    candidates = COMMON_SKILLS + (extra_skills or [])
    for skill in candidates:
        # word boundary matching, allow dashes/dots in skill names
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, text_lower) or re.search(pattern, tag_candidates.lower()):
            skills_set.add(skill.lower())
    return sorted(skills_set)


def standardize_location(loc: Optional[str]) -> str:
    """
    Normalize common location formats. For now, simple cleaning and
    mark 'remote' where indicated.
    """
    if not loc:
        return ""
    l = loc.strip().lower()
    l = re.sub(r"\s+", " ", l)
    # Common remote indicators
    if any(tok in l for tok in ("remote", "anywhere", "worldwide", "work from home")):
        return "Remote"
    # Keep country/city strings as-is but title-case them
    return l.title()


def parse_salary(s: Optional[str]) -> Dict[str, Optional[float]]:
    """
    Parse a variety of salary formats into min, max, currency (best-effort).
    Returns dict: {'min': float|None, 'max': float|None, 'currency': str|None}
    """
    if not s or not isinstance(s, str) or not s.strip():
        return {"min": None, "max": None, "currency": None}
    s_clean = s.replace(",", "").lower()
    # currency detection
    currency = None
    if "$" in s or "usd" in s_clean:
        currency = "USD"
    elif "€" in s or "eur" in s_clean:
        currency = "EUR"
    # numbers: capture 50k, 50000, 50,000 etc.
    nums = re.findall(r"(\d+(?:\.\d+)?)(k)?", s_clean)
    values = []
    for num, k in nums:
        v = float(num)
        if k == "k":
            v = v * 1000.0
        values.append(v)
    if len(values) == 0:
        return {"min": None, "max": None, "currency": currency}
    if len(values) == 1:
        return {"min": values[0], "max": values[0], "currency": currency}
    return {"min": min(values), "max": max(values), "currency": currency}


def infer_seniority(title: str) -> str:
    if not title:
        return ""
    t = title.lower()
    for k, v in SENIORITY_MAP.items():
        if k in t:
            return v
    return "mid"  # default to mid-level if unknown


def transform_records(records: List[Dict], extra_skills: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Transform raw job dictionaries into a structured DataFrame.
    """
    out = []
    for r in records:
        desc = clean_text(r.get("description_text") or r.get("description") or "")
        tags = r.get("tags") or ""
        title = clean_text(r.get("title") or "")
        company = clean_text(r.get("company_name") or r.get("company") or "")
        loc = standardize_location(r.get("candidate_required_location") or r.get("location") or "")
        pub_date = parse_publication_date(r.get("publication_date") or r.get("date") or None)
        salary = parse_salary(r.get("salary"))
        skills = extract_skills(desc, tags, extra_skills=extra_skills)
        seniority = infer_seniority(title)
        remote_flag = True if loc == "Remote" else False

        out.append({
            "id": r.get("id"),
            "url": r.get("url"),
            "title": title,
            "normalized_title": title.lower(),
            "company_name": company,
            "category": r.get("category"),
            "job_type": r.get("job_type"),
            "publication_date": pub_date,
            "location": loc,
            "remote": remote_flag,
            "salary_min": salary["min"],
            "salary_max": salary["max"],
            "salary_currency": salary["currency"],
            "description": desc,
            "tags": tags,
            "skills": ", ".join(skills),
            "seniority": seniority,
            # keep raw for debugging
            "raw_record": r,
        })
    df = pd.DataFrame(out)
    # Dedupe: prefer unique id when present, else by title+company+location
    if "id" in df.columns and df["id"].notna().any():
        df = df.drop_duplicates(subset=["id"])
    else:
        df = df.drop_duplicates(subset=["title", "company_name", "location"])
    # Convert publication_date to ISO string for CSV export
    df["publication_date"] = df["publication_date"].apply(lambda d: d.isoformat() if pd.notnull(d) else None)
    return df


def save_df(df: pd.DataFrame, output: str) -> None:
    os.makedirs(os.path.dirname(output), exist_ok=True)
    df.to_csv(output, index=False)
    print(f"Saved {len(df)} rows to {output}")


def cli():
    parser = argparse.ArgumentParser(description="Transform raw job records into cleaned CSV")
    parser.add_argument("--input", required=True, help="Path to raw input JSON or CSV")
    parser.add_argument("--output", required=True, help="Path to cleaned CSV output")
    parser.add_argument("--extra-skills-file", help="Optional newline-separated skills file")
    args = parser.parse_args()
    extra_skills = None
    if args.extra_skills_file:
        with open(args.extra_skills_file, "r", encoding="utf-8") as f:
            extra_skills = [ln.strip() for ln in f if ln.strip()]
    records = load_raw(args.input)
    df = transform_records(records, extra_skills=extra_skills)
    save_df(df, args.output)


if __name__ == "__main__":
    cli()
