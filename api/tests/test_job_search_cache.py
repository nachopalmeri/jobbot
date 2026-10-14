import unittest
from unittest.mock import patch

from api.routes.jobs import _serialize_job, search_jobs
from job_bot.job_scraper import JobScraper


class FakeDatabase:
    def __init__(self, custom_feeds=()):
        self.usage_checks = 0
        self.usage_increments = 0
        self.custom_feeds = list(custom_feeds)

    def get_user(self, telegram_id):
        return {"location": "Buenos Aires Argentina"}

    def check_usage_limit(self, telegram_id, resource):
        self.usage_checks += 1
        return True

    def get_user_profile(self, telegram_id):
        return {
            "experience_level": "junior",
            "role_type": "",
            "technologies": "",
            "job_modality": "cualquiera",
            "match_threshold": 50,
            "max_job_age_days": 30,
        }

    def get_user_keywords(self, telegram_id):
        return ["python junior"]

    def get_custom_feeds(self, telegram_id):
        return self.custom_feeds

    def generate_smart_keywords(self, telegram_id):
        return []

    def increment_usage(self, telegram_id, resource):
        self.usage_increments += 1


class FakeScraper:
    def __init__(self, jobs=()):
        self.jobs = list(jobs)
        self.search_calls = []
        self.last_search_metrics = []

    def search_all(
        self, keywords, location, max_age_days, include_role_taxonomy=True
    ):
        self.search_calls.append((keywords, include_role_taxonomy))
        return self.jobs

    def search_custom_rss(self, feed_url, feed_name):
        return [
            {
                "title": "AI Operations Intern",
                "company": "Example Startup",
                "location": "Argentina",
                "description": "Part-time AI workflow role",
                "url": "https://jobs.example.com/ai-intern",
                "source": feed_name,
            }
        ]

    def _safe_search(self, source_name, func, results, *args):
        jobs = func(*args)
        results.extend(jobs)
        self.last_search_metrics.append(
            {"source": source_name, "status": "ok", "jobs_count": len(jobs), "duration_ms": 0}
        )

    def _dedupe_jobs(self, jobs):
        return JobScraper()._dedupe_jobs(jobs)


class SearchCacheTests(unittest.IsolatedAsyncioTestCase):
    def test_serializes_structured_salary_without_inventing_currency(self):
        job = {
            "title": "Part-time QA",
            "salary_min": 20,
            "salary_max": 30,
            "salary_currency": None,
            "source": "Get on Board",
            "sources": ["Get on Board", "Custom RSS"],
        }

        result = _serialize_job(job, 80)

        self.assertEqual(result["salary_min"], 20)
        self.assertEqual(result["salary_max"], 30)
        self.assertIsNone(result["salary_currency"])
        self.assertEqual(result["sources"], ["Get on Board", "Custom RSS"])

    async def test_each_search_checks_and_consumes_quota(self):
        database = FakeDatabase()
        user = {"telegram_id": 42, "plan": "premium"}

        for _ in range(2):
            await search_jobs(
                q="python",
                modality="all",
                schedule="all",
                location="Buenos Aires Argentina",
                limit=20,
                offset=0,
                max_age_days=30,
                match_threshold=50,
                tags=None,
                db=database,
                scraper=FakeScraper(),
                current_user=user,
            )

        self.assertEqual(database.usage_checks, 2)
        self.assertEqual(database.usage_increments, 2)

    async def test_part_time_jobs_are_prioritized_over_full_time(self):
        database = FakeDatabase()
        jobs = [
            {
                "title": "Software Engineer Full-Time",
                "company": "Example",
                "location": "Buenos Aires",
                "description": "Full-time role",
                "url": "https://example.com/full-time",
            },
            {
                "title": "QA Tester Part-Time",
                "company": "Example",
                "location": "Buenos Aires",
                "description": "Part-time role",
                "url": "https://example.com/part-time",
            },
        ]

        with patch("api.routes.jobs._score_job", return_value=75):
            response = await search_jobs(
                q="",
                modality="all",
                schedule="all",
                location="Buenos Aires Argentina",
                limit=20,
                offset=0,
                max_age_days=30,
                match_threshold=50,
                tags=None,
                db=database,
                scraper=FakeScraper(jobs),
                current_user={"telegram_id": 42, "plan": "premium"},
            )

        self.assertEqual(
            [job["title"] for job in response["jobs"]],
            ["QA Tester Part-Time"],
        )

    async def test_full_time_without_salary_requires_clearly_high_match(self):
        jobs = [
            {
                "title": "Full-time Analyst",
                "company": "Example",
                "location": "Argentina",
                "employment_type": "full_time",
                "url": "https://example.com/role",
            }
        ]
        with patch("api.routes.jobs._score_job", return_value=84):
            response = await search_jobs(
                q="",
                modality="all",
                schedule="all",
                location="Argentina",
                limit=20,
                offset=0,
                max_age_days=30,
                match_threshold=50,
                tags=None,
                db=FakeDatabase(),
                scraper=FakeScraper(jobs),
                current_user={"telegram_id": 42, "plan": "premium"},
            )
        self.assertEqual(response["total"], 0)

        with patch("api.routes.jobs._score_job", return_value=85):
            response = await search_jobs(
                q="",
                modality="all",
                schedule="all",
                location="Argentina",
                limit=20,
                offset=0,
                max_age_days=30,
                match_threshold=50,
                tags=None,
                db=FakeDatabase(),
                scraper=FakeScraper(jobs),
                current_user={"telegram_id": 42, "plan": "premium"},
            )
        self.assertEqual(response["total"], 1)
        self.assertEqual(response["jobs"][0]["salary_status"], "not_reported")

    async def test_search_includes_user_custom_rss_feeds(self):
        existing_job = {
            "title": "AI Operations Intern",
            "company": "Example Startup",
            "location": "Argentina",
            "description": "Part-time AI workflow role",
            "url": "https://jobs.example.com/ai-intern",
            "source": "Get on Board",
        }
        with patch("api.routes.jobs._score_job", return_value=80):
            response = await search_jobs(
                q="",
                modality="all",
                schedule="all",
                location="Buenos Aires Argentina",
                limit=20,
                offset=0,
                max_age_days=30,
                match_threshold=50,
                tags=None,
                db=FakeDatabase(
                    [{"feed_url": "https://jobs.example.com/rss", "feed_name": "Example"}]
                ),
                scraper=FakeScraper(jobs=[existing_job]),
                current_user={"telegram_id": 42, "plan": "premium"},
            )

        self.assertEqual(response["total"], 1)
        self.assertEqual(response["jobs"][0]["sources"], ["Get on Board", "Example"])
        self.assertEqual(response["source_metrics"][0]["source"], "Example")
        self.assertEqual(response["source_metrics"][0]["jobs_count"], 1)

    async def test_custom_rss_obeys_location_and_age_filters(self):
        jobs = [
            {
                "title": "Old Argentina role",
                "company": "Example",
                "location": "Argentina",
                "date": "2020-01-01",
                "url": "https://example.com/old",
            },
            {
                "title": "US role",
                "company": "Example",
                "location": "New York, United States",
                "date": "2026-10-13",
                "url": "https://example.com/us",
            },
            {
                "title": "Fresh Argentina role",
                "company": "Example",
                "location": "Argentina",
                "date": "2026-10-13",
                "url": "https://example.com/fresh",
            },
        ]
        scraper = FakeScraper()
        scraper.search_custom_rss = lambda feed_url, feed_name: jobs
        with patch("api.routes.jobs._score_job", return_value=85):
            response = await search_jobs(
                q="",
                modality="all",
                schedule="all",
                location="Buenos Aires Argentina",
                limit=20,
                offset=0,
                max_age_days=30,
                match_threshold=50,
                tags=None,
                db=FakeDatabase([{"feed_url": "https://example.com/rss", "feed_name": "Example"}]),
                scraper=scraper,
                current_user={"telegram_id": 42, "plan": "premium"},
            )

        self.assertEqual([job["title"] for job in response["jobs"]], ["Fresh Argentina role"])

    async def test_explicit_query_does_not_expand_general_role_taxonomy(self):
        scraper = FakeScraper()

        await search_jobs(
            q="network engineer",
            modality="all",
            schedule="all",
            location="Buenos Aires Argentina",
            limit=20,
            offset=0,
            max_age_days=30,
            match_threshold=50,
            tags=None,
            db=FakeDatabase(),
            scraper=scraper,
            current_user={"telegram_id": 42, "plan": "premium"},
        )

        self.assertEqual(
            scraper.search_calls,
            [(["network engineer"], False)],
        )

    async def test_broad_search_keeps_roles_outside_current_profile_taxonomy(self):
        database = FakeDatabase()
        database.get_user_profile = lambda telegram_id: {
            "experience_level": "junior",
            "role_type": "backend developer",
            "technologies": "python, fastapi",
            "job_modality": "cualquiera",
            "match_threshold": 50,
            "max_job_age_days": 30,
        }
        scraper = FakeScraper(
            jobs=[
                {
                    "title": "AI Operations Assistant",
                    "company": "Startup",
                    "location": "Argentina",
                    "description": "Improve processes with automation",
                    "url": "https://example.com/ai-ops",
                }
            ]
        )

        with patch("api.routes.jobs._score_job", return_value=75):
            response = await search_jobs(
                q="",
                modality="all",
                schedule="all",
                location="Buenos Aires Argentina",
                limit=20,
                offset=0,
                max_age_days=30,
                match_threshold=50,
                tags=None,
                db=database,
                scraper=scraper,
                current_user={"telegram_id": 42, "plan": "premium"},
            )

        self.assertEqual(response["total"], 1)
        self.assertEqual(response["jobs"][0]["profile_relevance"], "exploratory")


if __name__ == "__main__":
    unittest.main()
