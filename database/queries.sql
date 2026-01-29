-- database/queries.sql
-- Example analytical queries for the Job Market Analytics pipeline

-- 1. Count jobs by category
SELECT category, COUNT(*) AS job_count
FROM jobs
GROUP BY category
ORDER BY job_count DESC;

-- 2. Top 20 companies by number of postings
SELECT company_name, COUNT(*) AS postings
FROM jobs
GROUP BY company_name
ORDER BY postings DESC
LIMIT 20;

-- 3. Top skills (naive split on comma)
-- Note: for better performance, use a skills table and normalization.
SELECT skills, COUNT(*) AS occurrences
FROM jobs
WHERE skills IS NOT NULL AND skills <> ''
GROUP BY skills
ORDER BY occurrences DESC
LIMIT 50;

-- 4. Salary statistics (USD only)
SELECT COUNT(*) AS n, AVG(salary_min) AS avg_min, AVG(salary_max) AS avg_max
FROM jobs
WHERE salary_currency = 'USD' AND salary_min IS NOT NULL;

-- 5. Remote vs On-site counts
SELECT remote, COUNT(*) AS count
FROM jobs
GROUP BY remote;
