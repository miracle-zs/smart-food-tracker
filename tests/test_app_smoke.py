def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_serves_dashboard_shell(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "SmartFood Tracker" in response.text
