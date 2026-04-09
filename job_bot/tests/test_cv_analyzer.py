from job_bot.cv_analyzer import compare_cv_with_offer


def test_compare_cv_with_offer_penalizes_role_and_seniority_mismatch():
    cv_text = """
    Junior backend developer with Python, FastAPI, SQL and Docker.
    Built APIs and internal automation tools.
    """
    offer_text = """
    Senior Frontend Engineer needed. Must have React, TypeScript, Next.js,
    design systems and strong frontend architecture experience.
    """

    analysis = compare_cv_with_offer(cv_text, offer_text)

    assert analysis["score"] < 40
    assert analysis["penalties"]
    assert any("rol" in item.lower() or "seniority" in item.lower() for item in analysis["suggestions"])


def test_compare_cv_with_offer_rewards_relevant_alignment():
    cv_text = """
    Backend engineer with Python, FastAPI, PostgreSQL, Docker and APIs.
    Improved API performance and built internal services.
    """
    offer_text = """
    Backend Engineer with Python, FastAPI, PostgreSQL and Docker.
    Need experience building APIs and microservices.
    """

    analysis = compare_cv_with_offer(cv_text, offer_text)

    assert analysis["score"] >= 70
    assert "python" in analysis["matching"]
