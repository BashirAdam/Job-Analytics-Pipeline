-- database/schema.sql
-- Create jobs table with fields produced by transformer

CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    url TEXT,
    title TEXT,
    normalized_title TEXT,
    company_name TEXT,
    category TEXT,
    job_type TEXT,
    publication_date DATETIME,
    location TEXT,
    remote BOOLEAN,
    salary_min REAL,
    salary_max REAL,
    salary_currency TEXT,
    description TEXT,
    tags TEXT,
    skills TEXT,
    seniority TEXT,
    created_at DATETIME DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_jobs_publication_date ON jobs(publication_date);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company_name);
CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location);
