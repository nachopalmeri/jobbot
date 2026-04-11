from job_scraper import JobScraper

jobs = [
    {"title": "Recent ISO", "date": "2026-03-01T10:00:00Z"},
    {"title": "Old ISO", "date": "2025-01-01T10:00:00Z"},
    {"title": "Recent RSS", "date": "Sun, 08 Mar 2026 12:34:56 GMT"},
    {"title": "Old RSS", "date": "Sun, 08 Mar 2025 12:34:56 GMT"},
    {"title": "No Date", "date": ""},
    {"title": "Bad Date", "date": "Not a date format"}
]

filtered = JobScraper.apply_date_filter(jobs, max_days=45)
print("Before filtering:", len(jobs))
print("After filtering:", len(filtered))
for job in filtered:
    print(f" - {job['title']}")
