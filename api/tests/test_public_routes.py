def test_health_endpoints_are_available(client):
    health = client.get("/health")
    live = client.get("/health/live")
    ready = client.get("/health/ready")

    assert health.status_code == 200
    assert live.status_code == 200
    assert ready.status_code == 200
    assert live.json()["status"] == "alive"
    assert ready.json()["status"] in {"ready", "not_ready"}
