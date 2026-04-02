import unittest
from job_bot.job_scraper import JobScraper

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

    def test_dedupe_jobs_falls_back_to_title_company_location(self):
        scraper = JobScraper()
        jobs = [
            {"title": "Data Engineer", "company": "Acme", "location": "Remote", "url": ""},
            {"title": "Data Engineer", "company": "Acme", "location": "Remote", "url": ""},
            {"title": "Data Engineer", "company": "Acme", "location": "USA", "url": ""},
        ]
        deduped = scraper._dedupe_jobs(jobs)
        self.assertEqual(len(deduped), 2)

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
