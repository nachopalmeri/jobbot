import unittest
import sqlite3
import os
from job_bot.database import Database

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_temp.db"
        self.db = Database(self.db_path)

    def tearDown(self):
        # On Windows, the file might be locked for a split second
        import time
        for i in range(5):
            try:
                if os.path.exists(self.db_path):
                    os.remove(self.db_path)
                break
            except PermissionError:
                time.sleep(0.1)

    def test_create_user(self):
        self.db.create_user_if_not_exists(123, "Test User")
        user = self.db.get_user(123)
        self.assertEqual(user["name"], "Test User")
        # Por defecto, los usuarios nuevos empiezan buscando trabajos remotos
        self.assertEqual(user["job_modality"], "remoto")

    def test_set_user_profile(self):
        self.db.create_user_if_not_exists(123, "Test User")
        self.db.set_user_profile(123, "senior", "backend", "python, sqlite", "remoto", 15)
        profile = self.db.get_user_profile(123)
        self.assertEqual(profile["experience_level"], "senior")
        self.assertEqual(profile["job_modality"], "remoto")
        self.assertEqual(profile["max_job_age_days"], 15)

    def test_delete_user_data(self):
        self.db.create_user_if_not_exists(123, "Test User")
        self.db.delete_user_data(123)
        user = self.db.get_user(123)
        self.assertIsNone(user)

if __name__ == "__main__":
    unittest.main()
