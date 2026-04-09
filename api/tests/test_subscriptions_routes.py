from api.routes.auth import create_access_token


def test_plans_endpoint_exposes_cv_suite_in_premium(client):
    response = client.get("/subscriptions/plans")

    assert response.status_code == 200
    payload = response.json()
    plans = {plan["id"]: plan for plan in payload["plans"]}

    assert "3 busquedas guiadas por dia" in plans["free"]["features"]
    assert plans["starter"]["price"] == 4
    assert plans["starter"]["yearly_price"] == 40
    assert plans["pro"]["price"] == 8
    assert plans["pro"]["yearly_price"] == 80
    assert plans["premium"]["price"] == 12
    assert plans["premium"]["yearly_price"] == 120
    assert "CV Intelligence Suite destacada" in plans["premium"]["features"]
    assert "120 busquedas por dia" in plans["premium"]["features"]


def test_checkout_rejects_invalid_billing_cycle(client, registered_user):
    auth_headers = {
        "Authorization": f"Bearer {create_access_token({'sub': registered_user['email'], 'telegram_id': registered_user['telegram_id']})}"
    }
    response = client.post(
        "/subscriptions/create-checkout",
        headers=auth_headers,
        json={
            "provider": "stripe",
            "plan": "pro",
            "billing_cycle": "weekly",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Ciclo de facturacion no valido"
