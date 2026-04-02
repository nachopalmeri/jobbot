import os
import tempfile
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.routes import auth
from job_bot.database import Database


os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-min-32-chars-long")
os.environ.setdefault("APP_ENV", "testing")


@pytest.fixture
def temp_db() -> Generator[Database, None, None]:
    with tempfile.NamedTemporaryFile(suffix=".db") as db_file:
        yield Database(db_path=db_file.name, db_type="sqlite")


@pytest.fixture
def client(temp_db: Database) -> Generator[TestClient, None, None]:
    app.dependency_overrides[auth.get_db] = lambda: temp_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def registered_user(temp_db: Database) -> dict:
    telegram_id = 6722199376
    temp_db.create_user_if_not_exists(telegram_id, "Pisculichi")
    temp_db.create_web_user(telegram_id, "paradonista@gmail.com", auth.get_password_hash("lulita"))
    temp_db.set_alert_channel(telegram_id, "telegram")
    temp_db.update_user_plan(telegram_id, "premium")
    return {
        "telegram_id": telegram_id,
        "email": "paradonista@gmail.com",
        "plan": "premium",
        "is_admin": False,
        "has_telegram_link": True,
        "name": "Pisculichi",
        "user": temp_db.get_user(telegram_id),
        "web_user": temp_db.get_web_user(telegram_id),
    }
