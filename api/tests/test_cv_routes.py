from api.main import app
from api.routes import auth, cv


def test_scan_basic_returns_scores_and_quota(client, temp_db, registered_user):
    app.dependency_overrides[auth.get_authenticated_user] = lambda: registered_user

    response = client.post(
        "/cv/scan",
        data={
            "cv_text": """
            Juan Perez
            juan@example.com
            LinkedIn: linkedin.com/in/juan
            Summary: Backend engineer with Python and FastAPI experience.
            Experience: Built APIs, improved performance 25%, automated reports.
            Education: Computer Science
            Skills: Python, FastAPI, SQL, Docker
            """,
            "job_description": "Buscamos backend engineer con Python, FastAPI y SQL.",
            "job_title": "Backend Engineer",
            "company_name": "Acme",
            "mode": "basic",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "basic"
    assert payload["ats_score"] > 0
    assert payload["match_score"] is not None
    assert "python" in [keyword.lower() for keyword in payload["matching_keywords"]]
    assert payload["ai_feedback_included"] is False
    assert payload["quota"]["limit"] >= payload["quota"]["used"]


def test_scan_pro_uses_plan_quota_and_returns_ai_feedback(client, temp_db, registered_user, monkeypatch):
    app.dependency_overrides[auth.get_authenticated_user] = lambda: registered_user

    async def fake_analyze_with_groq(_: str) -> str:
        return "Diagnostico corto. Mejora bullets y keywords."

    monkeypatch.setattr(cv, "analyze_with_groq", fake_analyze_with_groq)

    response = client.post(
        "/cv/scan",
        data={
            "cv_text": """
            Juana Gomez
            juana@example.com
            Experience: Implemented Python APIs and reduced latency 30%.
            Skills: Python, FastAPI, PostgreSQL, Docker
            """,
            "job_description": "Senior backend con Python, FastAPI y PostgreSQL.",
            "job_title": "Senior Backend",
            "company_name": "Nova",
            "mode": "pro",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "pro"
    assert payload["ai_feedback_included"] is True
    assert payload["used_credits"] is False
    assert payload["ai_feedback"] == "Diagnostico corto. Mejora bullets y keywords."
    assert payload["quota"]["used"] >= 1


def test_scan_requires_cv_input(client, registered_user):
    app.dependency_overrides[auth.get_authenticated_user] = lambda: registered_user

    response = client.post("/cv/scan", data={"mode": "basic"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Necesitamos el texto o archivo de tu CV"
