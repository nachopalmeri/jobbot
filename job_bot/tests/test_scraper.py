import datetime
import unittest
from unittest.mock import patch
from job_bot.job_scraper import JobScraper
from job_bot import config

class TestJobScraper(unittest.TestCase):
    def test_extract_domain(self):
        self.assertEqual(JobScraper.extract_domain("apple.com"), "apple.com")
        self.assertEqual(
            JobScraper.extract_domain("https://www.apple.com/careers"),
            "apple.com",
        )
        self.assertEqual(JobScraper.extract_domain(""), "")

    def test_apply_modality_filter(self):
        jobs = [
            {"title": "Dev Python", "location": "Remoto", "description": "Trabajo 100% remoto", "source": "Remotive"},
            {"title": "Frontend dev", "location": "Buenos Aires", "description": "Presencial flex", "source": "LinkedIn"},
            {"title": "Java Dev", "location": "Híbrido", "description": "2 dias en oficina", "source": "LinkedIn"},
        ]
        
        # Test Remoto
        remote_jobs = JobScraper.apply_modality_filter(jobs, "remoto")
        self.assertEqual(len(remote_jobs), 1)
        self.assertEqual(remote_jobs[0]["source"], "Remotive")
        
        # Test Presencial (heuristic: not remote, not hybrid)
        presencial_jobs = JobScraper.apply_modality_filter(jobs, "presencial")
        self.assertTrue(len(presencial_jobs) >= 1)
        
        # Test Cualquiera
        any_jobs = JobScraper.apply_modality_filter(jobs, "cualquiera")
        self.assertEqual(len(any_jobs), 3)

    def test_location_filter_marks_remote_without_country_as_uncertain(self):
        jobs = [
            {"title": "Remote role", "location": "Remote"},
            {"title": "Argentina role", "location": "Remote in Argentina"},
            {"title": "Unknown location", "location": ""},
            {"title": "US onsite", "location": "New York, United States"},
        ]

        result = JobScraper.apply_location_filter(jobs, "Buenos Aires Argentina")

        self.assertEqual([job["title"] for job in result], ["Remote role", "Argentina role", "Unknown location"])
        self.assertEqual(result[0]["location_match"], "unknown")
        self.assertEqual(result[1]["location_match"], "eligible")
        self.assertEqual(result[2]["location_match"], "unknown")

    def test_apply_schedule_filter(self):
        jobs = [
            {"title": "Backend Developer", "location": "Remote", "description": "Full time remote role"},
            {"title": "Soporte IT", "location": "CABA", "description": "Media jornada presencial"},
            {"title": "QA Analyst", "location": "Hybrid", "description": "Part-time hybrid role"},
            {"title": "Data Analyst", "location": "Argentina", "description": "Schedule not stated"},
        ]

        full_time_jobs = JobScraper.apply_schedule_filter(jobs, "full_time")
        self.assertEqual(len(full_time_jobs), 1)
        self.assertIn("Full time", full_time_jobs[0]["description"])

        part_time_jobs = JobScraper.apply_schedule_filter(jobs, "part_time")
        self.assertEqual(len(part_time_jobs), 2)

    def test_apply_schedule_filter_uses_structured_employment_type(self):
        jobs = [
            {"title": "QA Engineer", "employment_type": "part_time"},
            {"title": "Support Analyst", "employment_type": "full_time"},
        ]

        part_time_jobs = JobScraper.apply_schedule_filter(jobs, "part_time")

        self.assertEqual(part_time_jobs, [jobs[0]])

    def test_part_time_results_are_ranked_before_full_time_and_unknown(self):
        jobs = [
            {"title": "Senior but strong match", "description": "Full-time", "match_score": 95},
            {"title": "Unknown schedule", "description": "", "match_score": 99},
            {"title": "QA part-time", "description": "", "match_score": 70},
            {"title": "AI part-time", "description": "", "match_score": 85},
        ]

        ranked = JobScraper.prioritize_part_time(jobs)

        self.assertEqual(
            [job["title"] for job in ranked],
            ["AI part-time", "QA part-time", "Unknown schedule", "Senior but strong match"],
        )

    def test_apply_profile_relevance_filter(self):
        jobs = [
            {"title": "Backend Python Developer", "description": "Python, FastAPI, PostgreSQL"},
            {"title": "Diseñador UX", "description": "Figma, research, design systems"},
            {"title": "Data Analyst", "description": "SQL, dashboards, analytics"},
        ]

        filtered = JobScraper.apply_profile_relevance_filter(
            jobs,
            role_type="backend",
            technologies="python, fastapi",
        )
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["title"], "Backend Python Developer")

    def test_profile_relevance_annotation_keeps_exploratory_roles_visible(self):
        jobs = [
            {"title": "Backend Python Developer", "description": "Python, FastAPI, PostgreSQL"},
            {"title": "Diseñador UX", "description": "Figma, research, design systems"},
            {"title": "Data Analyst", "description": "SQL, dashboards, analytics"},
        ]

        annotated = JobScraper.annotate_profile_relevance(
            jobs,
            role_type="backend",
            technologies="python, fastapi",
        )

        self.assertEqual(len(annotated), 3)
        relevance_by_title = {job["title"]: job["profile_relevance"] for job in annotated}
        self.assertEqual(relevance_by_title["Backend Python Developer"], "strong")
        self.assertEqual(relevance_by_title["Diseñador UX"], "exploratory")
        self.assertEqual(relevance_by_title["Data Analyst"], "exploratory")

    def test_apply_negative_filter(self):
        jobs = [
            {"title": "Junior Python Dev", "description": ""},
            {"title": "Senior Python Dev", "description": ""},
        ]
        # Filter Senior for Junior level
        filtered = JobScraper.apply_negative_filter(jobs, "junior")
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["title"], "Junior Python Dev")

    def test_company_enrichment_uses_cache(self):
        scraper = JobScraper()
        expected = {
            "domain": "apple.com",
            "name": "Apple",
            "headline": "",
            "description": "",
            "industry": "",
            "size": "",
            "website": "",
            "linkedin_url": "",
            "location": "",
            "founded": "",
            "logo": "",
            "raw": {"name": "Apple"},
        }
        scraper._cache_set(
            "company:apple.com",
            expected,
            ttl_seconds=60,
        )

        result = scraper.enrich_company_by_domain("https://apple.com")
        self.assertEqual(result["name"], "Apple")
        self.assertEqual(result["domain"], "apple.com")

    def test_search_getonbrd_normalizes_public_jobs(self):
        scraper = JobScraper()
        response = {
            "data": [
                {
                    "id": "job-123",
                    "attributes": {
                        "title": "Part-time QA Engineer",
                        "description": "Test automation",
                        "remote": True,
                        "remote_zone": "Argentina",
                        "countries": ["Argentina"],
                        "modality": {"data": {"type": "part_time"}},
                        "min_salary": 20,
                        "max_salary": 30,
                        "published_at": 1791849600,
                        "company": {
                            "data": {"attributes": {"name": "Example AI"}}
                        },
                    },
                    "links": {"public_url": "https://www.getonbrd.com/jobs/job-123"},
                }
            ]
        }

        with patch.object(scraper, "_requests_get_json", return_value=response) as get_json:
            jobs = scraper.search_getonbrd("part-time QA")

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["title"], "Part-time QA Engineer")
        self.assertEqual(jobs[0]["company"], "Example AI")
        self.assertIn("Argentina", jobs[0]["location"])
        self.assertEqual(jobs[0]["employment_type"], "part_time")
        self.assertEqual(jobs[0]["salary_min"], 20)
        self.assertIsNone(jobs[0]["salary_currency"])
        self.assertEqual(jobs[0]["url"], "https://www.getonbrd.com/jobs/job-123")
        get_json.assert_called_once_with(
            "https://www.getonbrd.com/api/v0/search/jobs",
            params={
                "query": "part-time QA",
                "country_code": "ar",
                "page": 1,
                "per_page": 10,
                "lang": "en",
                "expand": '["company"]',
            },
        )

    def test_explicit_query_does_not_add_unrelated_getonbrd_schedule_queries(self):
        scraper = JobScraper()
        calls = []

        def capture_search(source_name, function, results, *args):
            calls.append((source_name, args))

        with patch.dict(config.SOURCES_ENABLED, {"getonbrd": True}, clear=True):
            with patch.object(config, "PREMIUM_BACKFILL_MIN_RESULTS", 0):
                with patch("job_bot.job_scraper.time.sleep"):
                    with patch.object(scraper, "_safe_search", side_effect=capture_search):
                        scraper.search_all(
                            ["network engineer"],
                            "Argentina",
                            include_role_taxonomy=False,
                        )

        self.assertEqual(calls, [])

    def test_premium_backfill_is_limited_to_one_query_per_search(self):
        scraper = JobScraper()
        premium_queries = []

        def capture_search(source_name, function, results, *args):
            if source_name == "Premium Backfill":
                premium_queries.append(args[0])

        with patch.dict(config.SOURCES_ENABLED, {}, clear=True):
            with patch.object(config, "PREMIUM_BACKFILL_MIN_RESULTS", 5):
                with patch("job_bot.job_scraper.time.sleep"):
                    with patch.object(scraper, "_safe_search", side_effect=capture_search):
                        scraper.search_all(["python junior"])

        self.assertEqual(len(premium_queries), 1)

    def test_dedupe_jobs_falls_back_to_title_company_location(self):
        scraper = JobScraper()
        jobs = [
            {"title": "Data Engineer", "company": "Acme", "location": "Remote", "url": ""},
            {"title": "Data Engineer", "company": "Acme", "location": "Remote", "url": ""},
            {"title": "Data Engineer", "company": "Acme", "location": "USA", "url": ""},
        ]
        deduped = scraper._dedupe_jobs(jobs)
        self.assertEqual(len(deduped), 2)

    def test_dedupe_jobs_keeps_all_source_provenance(self):
        scraper = JobScraper()
        jobs = [
            {"title": "AI Analyst", "company": "Acme", "url": "https://acme.com/job", "source": "Get on Board"},
            {"title": "AI Analyst", "company": "Acme", "url": "https://acme.com/job", "source": "Custom RSS"},
        ]

        deduped = scraper._dedupe_jobs(jobs)

        self.assertEqual(len(deduped), 1)
        self.assertEqual(deduped[0]["sources"], ["Get on Board", "Custom RSS"])

    def test_dedupe_jobs_ignores_tracking_parameters_and_fragments(self):
        scraper = JobScraper()
        jobs = [
            {
                "title": "AI Analyst",
                "company": "Acme",
                "url": "https://www.acme.com/jobs/1?utm_source=mail&ref=weekly#apply",
                "source": "RSS",
            },
            {
                "title": "AI Analyst",
                "company": "Acme",
                "url": "https://acme.com/jobs/1?ref=other&utm_campaign=jobs",
                "source": "Get on Board",
            },
        ]

        deduped = scraper._dedupe_jobs(jobs)

        self.assertEqual(len(deduped), 1)
        self.assertEqual(deduped[0]["sources"], ["RSS", "Get on Board"])
        self.assertTrue(deduped[0]["url"].startswith("https://www.acme.com/jobs/1?"))

    def test_parse_job_date_accepts_date_only_rfc822_and_epoch(self):
        self.assertEqual(
            JobScraper.parse_job_date("2026-10-13"),
            datetime.datetime(2026, 10, 13, tzinfo=datetime.timezone.utc),
        )
        self.assertEqual(
            JobScraper.parse_job_date("Tue, 13 Oct 2026 12:30:00 GMT"),
            datetime.datetime(2026, 10, 13, 12, 30, tzinfo=datetime.timezone.utc),
        )
        self.assertEqual(
            JobScraper.parse_job_date("1791892800"),
            datetime.datetime.fromtimestamp(1791892800, tz=datetime.timezone.utc),
        )
        self.assertEqual(
            JobScraper.parse_job_date("1791892800000"),
            datetime.datetime.fromtimestamp(1791892800, tz=datetime.timezone.utc),
        )
        self.assertIsNone(JobScraper.parse_job_date("2026"))
        self.assertIsNone(JobScraper.parse_job_date("not a date"))

    def test_apply_date_filter_marks_unknown_dates_instead_of_calling_them_recent(self):
        jobs = [{"title": "No date", "date": "unparseable"}]

        result = JobScraper.apply_date_filter(jobs, max_days=30)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["date_status"], "unknown")

    def test_safe_search_records_per_source_count_latency_and_failures(self):
        scraper = JobScraper()
        results = []

        scraper._safe_search("Public API", lambda: [{"title": "Role"}], results)
        scraper._safe_search(
            "Broken feed", lambda: (_ for _ in ()).throw(RuntimeError("offline")), results
        )

        self.assertEqual(results, [{"title": "Role"}])
        metrics = {metric["source"]: metric for metric in scraper.last_search_metrics}
        self.assertEqual(metrics["Public API"]["status"], "ok")
        self.assertEqual(metrics["Public API"]["jobs_count"], 1)
        self.assertGreaterEqual(metrics["Public API"]["duration_ms"], 0)
        self.assertTrue(metrics["Public API"]["checked_at"].endswith("+00:00"))
        self.assertEqual(metrics["Broken feed"]["status"], "error")
        self.assertEqual(metrics["Broken feed"]["error_type"], "RuntimeError")

    def test_safe_search_does_not_log_provider_exception_details(self):
        scraper = JobScraper()
        with patch("job_bot.job_scraper.logger.error") as log_error:
            scraper._safe_search(
                "Private feed",
                lambda: (_ for _ in ()).throw(ValueError("token=private-value")),
                [],
            )

        self.assertNotIn("private-value", str(log_error.call_args))

    def test_normalize_job_ignores_intermediary_domains(self):
        scraper = JobScraper()
        linkedin_job = scraper._normalize_job(
            {
                "title": "Backend Engineer",
                "company": "Ver en LinkedIn",
                "url": "https://www.linkedin.com/jobs/view/123",
            }
        )
        self.assertEqual(linkedin_job["company_domain"], "")

        direct_job = scraper._normalize_job(
            {
                "title": "Backend Engineer",
                "company": "Acme",
                "company_website": "https://www.acme.com/careers",
                "url": "https://jobs.acme.com/123",
            }
        )
        self.assertEqual(direct_job["company_domain"], "acme.com")

if __name__ == "__main__":
    unittest.main()
