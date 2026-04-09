"""
TDD Tests for Search Mode feature (/modo command)
"""

import unittest
import sqlite3
import os
import sys


# Mock config before importing database
class MockConfig:
    DATABASE_TYPE = "sqlite"
    DATABASE_PATH = ":memory:"
    DATABASE_URL = ""
    GROQ_API_KEY = ""
    GROQ_MODEL = "llama-3.3-70b-versatile"
    DEFAULT_LOCATION = "Buenos Aires"
    DEFAULT_KEYWORDS = ["python"]
    NEGATIVE_KEYWORDS = []
    LEVEL_NEGATIVE_KEYWORDS = {}
    LOCATION_VARIANTS = []
    GLOBAL_LOCATION_TERMS = {}
    SOURCES_ENABLED = {"remotive": True}
    REQUEST_DELAY_SECONDS = 1
    MAX_RESULTS_PER_SOURCE = 10
    MAX_JOBS_PER_NOTIFICATION = 5
    REQUEST_TIMEOUT = 5
    STATS_API_PORT = 8080
    STATS_API_ENABLED = True
    LANDING_URL = "http://localhost"
    MIN_CHECK_INTERVAL_HOURS = 3
    MAX_CHECK_INTERVAL_HOURS = 24
    DEFAULT_CHECK_INTERVAL_HOURS = 6
    SCHEDULER_POLL_MINUTES = 10


# Inject mock config
sys.modules["config"] = MockConfig()

from job_bot.database import Database


class TestSearchMode(unittest.TestCase):
    """Tests for set_search_mode and get_search_mode"""

    def setUp(self):
        """Create in-memory database for testing"""
        # Use file-based temp db instead of :memory: to ensure tables persist
        import tempfile

        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.db = Database(self.temp_db.name)

    def tearDown(self):
        """Clean up temp database"""
        import time

        for i in range(5):
            try:
                os.unlink(self.temp_db.name)
                break
            except PermissionError:
                time.sleep(0.1)

    def test_default_search_mode_is_calidad(self):
        """New users should have default search mode 'calidad'"""
        # Create user
        self.db.create_user_if_not_exists(123, "Test User")

        # Get search mode
        mode = self.db.get_search_mode(123)

        self.assertEqual(mode, "calidad")

    def test_set_search_mode_volumen(self):
        """Should be able to set search mode to 'volumen'"""
        self.db.create_user_if_not_exists(123, "Test User")

        # Set mode
        self.db.set_search_mode(123, "volumen")

        # Verify
        mode = self.db.get_search_mode(123)
        self.assertEqual(mode, "volumen")

    def test_set_search_mode_calidad(self):
        """Should be able to set search mode to 'calidad'"""
        self.db.create_user_if_not_exists(123, "Test User")

        # Set mode
        self.db.set_search_mode(123, "calidad")

        # Verify
        mode = self.db.get_search_mode(123)
        self.assertEqual(mode, "calidad")

    def test_invalid_search_mode_ignored(self):
        """Invalid modes should be ignored (not saved)"""
        self.db.create_user_if_not_exists(123, "Test User")

        # Try invalid mode
        self.db.set_search_mode(123, "invalid_mode")

        # Should still be default
        mode = self.db.get_search_mode(123)
        self.assertEqual(mode, "calidad")

    def test_search_mode_persists_after_update(self):
        """Search mode should persist when user updates profile"""
        self.db.create_user_if_not_exists(123, "Test User")

        # Set mode
        self.db.set_search_mode(123, "volumen")

        # Update profile (should not affect mode)
        self.db.set_user_profile(123, "junior", "backend", "python", "remoto", "cualquiera", 30)

        # Mode should still be volumen
        mode = self.db.get_search_mode(123)
        self.assertEqual(mode, "volumen")


if __name__ == "__main__":
    unittest.main()
