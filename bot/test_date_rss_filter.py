from job_scraper import JobScraper
import logging

logging.basicConfig(level=logging.DEBUG)

jobs = [
    {"title": "Old RSS", "date": "Sun, 08 Mar 2025 12:34:56 GMT"}
]

filtered = JobScraper.apply_date_filter(jobs, max_days=45)
print("Filtered:", filtered)
