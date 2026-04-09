from api.main import app
from api.routes import auth


def test_preferences_include_location(client, temp_db, registered_user):
    temp_db.set_user_location(registered_user["telegram_id"], "Cordoba, Argentina")
    app.dependency_overrides[auth.get_authenticated_user] = lambda: registered_user

    response = client.get("/users/preferences")

    assert response.status_code == 200
    payload = response.json()
    assert payload["location"] == "Cordoba, Argentina"


def test_preferences_persist_location_and_normalize_modality(client, temp_db, registered_user):
    app.dependency_overrides[auth.get_authenticated_user] = lambda: registered_user

    response = client.post(
        "/users/preferences",
        json={
            "location": "Montevideo, Uruguay",
            "experience_level": "junior",
            "role_type": "Backend Developer",
            "technologies": "Python, FastAPI",
            "job_modality": "remote",
            "job_schedule": "full-time",
            "max_job_age_days": 14,
            "match_threshold": 82,
            "alert_channel": "telegram",
            "check_interval_hours": 4,
            "alert_start_hour": 9,
            "alert_end_hour": 18,
            "timezone": "America/Montevideo",
            "weekly_goal": 7,
            "digest_mode": "daily",
            "active_alerts": True,
            "blocked_companies": "Foo Corp",
            "preferred_companies": "Bar Labs",
        },
    )

    assert response.status_code == 200
    saved_user = temp_db.get_user(registered_user["telegram_id"])
    assert saved_user["location"] == "Montevideo, Uruguay"
    assert saved_user["job_modality"] == "remoto"
    assert saved_user["job_schedule"] == "full_time"
