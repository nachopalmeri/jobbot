"""Helpers for tracking jobs already presented to a user."""

from typing import Dict, List, Protocol


class SeenJobsDatabase(Protocol):
    def is_job_seen(self, telegram_id: int, url: str) -> bool: ...

    def mark_job_seen(self, telegram_id: int, job: Dict) -> None: ...


def collect_new_jobs(
    jobs: List[Dict], database: SeenJobsDatabase, telegram_id: int
) -> List[Dict]:
    """Return unseen jobs and record each valid URL using the Database contract."""
    new_jobs = []
    for job in jobs:
        url = (job.get("url") or "").strip()
        if not url or database.is_job_seen(telegram_id, url):
            continue
        database.mark_job_seen(telegram_id, job)
        new_jobs.append(job)
    return new_jobs
