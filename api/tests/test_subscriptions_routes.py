def test_plans_endpoint_exposes_cv_suite_in_premium(client):
    response = client.get("/subscriptions/plans")

    assert response.status_code == 200
    payload = response.json()
    plans = {plan["id"]: plan for plan in payload["plans"]}

    assert plans["starter"]["price"] == 4
    assert plans["pro"]["price"] == 8
    assert plans["premium"]["price"] == 12
    assert "CV Intelligence Suite destacada" in plans["premium"]["features"]
    assert "Workflow completo para aplicar mejor" in plans["premium"]["features"]
