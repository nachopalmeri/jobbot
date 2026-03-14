import unittest
from job_scraper import JobScraper

class TestJobScraper(unittest.TestCase):
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

if __name__ == "__main__":
    unittest.main()
