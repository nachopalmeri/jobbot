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

    def test_link_web_account_to_telegram_migrates_data(self):
        self.db.create_user_if_not_exists(-1, "Web User")
        self.db.set_user_profile(-1, "senior", "backend", "python, fastapi", "remoto", 14, 80)
        self.db.set_user_keywords(-1, ["python senior", "fastapi remoto"])
        self.db.create_web_user(-1, "web@example.com", "hashed")
        self.db.update_user_plan(-1, "pro")

        result = self.db.link_web_account_to_telegram(-1, 123456, "Nacho")

        self.assertEqual(result["telegram_id"], 123456)
        self.assertEqual(result["plan"], "pro")
        self.assertEqual(self.db.get_web_user(-1), None)

        linked_user = self.db.get_user(123456)
        linked_web_user = self.db.get_web_user(123456)
        keywords = self.db.get_user_keywords(123456)

        self.assertEqual(linked_user["role_type"], "backend")
        self.assertEqual(linked_user["technologies"], "python, fastapi")
        self.assertEqual(linked_web_user["email"], "web@example.com")
        self.assertIn("python senior", keywords)
        self.assertIn("fastapi remoto", keywords)

if __name__ == "__main__":
    unittest.main()
