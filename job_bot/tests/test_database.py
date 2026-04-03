import unittest
import os
import tempfile
from job_bot.database import Database

class TestDatabase(unittest.TestCase):
    def setUp(self):
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        temp_file.close()
        self.db_path = temp_file.name
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
        # Por defecto, los usuarios nuevos arrancan sin restringir modalidad
        self.assertEqual(user["job_modality"], "cualquiera")
        self.assertEqual(user["job_schedule"], "cualquiera")

    def test_set_user_profile(self):
        self.db.create_user_if_not_exists(123, "Test User")
        self.db.set_user_profile(
            123,
            "senior",
            "backend",
            "python, sqlite",
            "remoto",
            "full_time",
            15,
        )
        profile = self.db.get_user_profile(123)
        self.assertEqual(profile["experience_level"], "senior")
        self.assertEqual(profile["job_modality"], "remoto")
        self.assertEqual(profile["job_schedule"], "full_time")
        self.assertEqual(profile["max_job_age_days"], 15)

    def test_delete_user_data(self):
        self.db.create_user_if_not_exists(123, "Test User")
        self.db.delete_user_data(123)
        user = self.db.get_user(123)
        self.assertIsNone(user)

if __name__ == "__main__":
    unittest.main()
