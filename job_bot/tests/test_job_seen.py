import unittest

from job_bot.job_seen import collect_new_jobs


class FakeDatabase:
    def __init__(self, seen_urls=()):
        self.seen_urls = set(seen_urls)
        self.marked_jobs = []

    def is_job_seen(self, telegram_id, url):
        return url in self.seen_urls

    def mark_job_seen(self, telegram_id, job):
        self.marked_jobs.append(job)
        self.seen_urls.add(job["url"])


class CollectNewJobsTests(unittest.TestCase):
    def test_uses_database_url_contract_and_marks_each_new_job_once(self):
        database = FakeDatabase(seen_urls={"https://example.com/old"})
        jobs = [
            {"title": "Already seen", "url": "https://example.com/old"},
            {"title": "New", "source": "Example", "url": "https://example.com/new"},
            {"title": "Duplicate in batch", "url": "https://example.com/new"},
            {"title": "Missing URL"},
        ]

        new_jobs = collect_new_jobs(jobs, database, telegram_id=42)

        self.assertEqual([job["title"] for job in new_jobs], ["New"])
        self.assertEqual(database.marked_jobs, [jobs[1]])


if __name__ == "__main__":
    unittest.main()
