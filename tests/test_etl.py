"""
tests/test_etl.py

Basic unit tests for transformer and extractor parsing logic.
Run: pytest -q
"""
from __future__ import annotations
import pandas as pd
from src import transformer


SAMPLE_RECORD = {
    "id": "abc-123",
    "url": "https://example.com/job/1",
    "title": "Senior Data Scientist",
    "company_name": "Acme Analytics",
    "category": "Data",
    "job_type": "Full-time",
    "publication_date": "2026-01-01T12:00:00",
    "candidate_required_location": "Worldwide",
    "salary": "$80k - $120k",
    "description_text": "We use Python, SQL and AWS. Experience with Spark is a plus.",
    "tags": "python, aws, sql",
}


def test_extract_skills_and_seniority():
    df = transformer.transform_records([SAMPLE_RECORD])
    assert len(df) == 1
    row = df.iloc[0]
    # Skills detection
    assert "python" in row["skills"]
    assert "aws" in row["skills"]
    # Seniority
    assert row["seniority"] == "senior"
    # Location normalized to Remote because 'Worldwide' appears
    assert row["location"] == "Remote"
    # Salary parsing
    assert row["salary_min"] == 80000.0
    assert row["salary_max"] == 120000.0


def test_clean_description_and_fields():
    df = transformer.transform_records([SAMPLE_RECORD])
    row = df.iloc[0]
    assert isinstance(row["description"], str) or row["description"] == ""
