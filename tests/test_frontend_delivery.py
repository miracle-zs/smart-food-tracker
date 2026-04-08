def test_dashboard_shell_serves_forms_and_item_board(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "SmartFood Tracker" in response.text
    assert "manual-entry-form" in response.text
    assert "voice-entry-form" in response.text
    assert "items-board" in response.text
    assert "/static/app.js" in response.text
