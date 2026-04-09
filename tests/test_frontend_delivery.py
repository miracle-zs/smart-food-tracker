def test_dashboard_shell_serves_forms_and_item_board(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "SmartFood Tracker" in response.text
    assert "manual-entry-form" in response.text
    assert "voice-entry-form" in response.text
    assert "summary-section" in response.text
    assert "risk-board-section" in response.text
    assert "pending-confirmation-section" in response.text
    assert "quick-intake-section" in response.text
    assert "inventory-section" in response.text
    assert "items-board" in response.text
    assert "edit-confirm-panel" in response.text
    assert "confirm-pending-item" in response.text
    assert "/static/app.js" in response.text


def test_dashboard_script_resets_review_panel_after_save_and_confirm(client):
    response = client.get("/static/app.js")

    assert response.status_code == 200
    script = response.text
    assert "function resetReviewPanel()" in script
    assert "pendingItemIdField.value = \"\";" in script
    assert "pendingItemNameField.disabled = true;" in script
    assert "confirmPendingButton.disabled = true;" in script
    assert "resetReviewPanel();" in script
