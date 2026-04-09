import pytest
from datetime import date, timedelta

from app.config import settings
from app.models.food_item import FoodItem


@pytest.mark.parametrize(
    "payload",
    [
        {"text": "今天放了一袋鸡柳在冷冻室"},
        {"raw_text": "今天放了一袋鸡柳在冷冻室"},
        {"query": {"text": "今天放了一袋鸡柳在冷冻室"}},
        {"text": {"content": "今天放了一袋鸡柳在冷冻室"}},
        {"raw_text": ["ignored", {"message": "今天放了一袋鸡柳在冷冻室"}]},
        {"content": "今天放了一袋鸡柳在冷冻室"},
        {"message": "今天放了一袋鸡柳在冷冻室"},
    ],
)
def test_webhook_ingestion_accepts_common_text_payloads(client, db_session, payload):
    response = client.post(
        "/api/items/voice/webhook",
        json=payload,
    )

    assert response.status_code == 201
    assert response.json() == {"ok": True, "item_id": 1}

    item = db_session.query(FoodItem).one()
    assert item.name == "鸡柳"
    assert item.location == "冷冻室"
    assert item.expiry_date == date.today() + timedelta(days=30)
    assert item.needs_confirmation is True


def test_webhook_ingestion_rejects_payloads_without_text(client):
    response = client.post("/api/items/voice/webhook", json={})

    assert response.status_code == 422
    assert response.json()["detail"] == "Webhook payload must include text content"


def test_xiaoai_webhook_requires_server_token_configuration(client):
    response = client.post(
        "/api/items/xiaoai/voice/webhook",
        json={"text": "今天放了一袋鸡柳在冷冻室"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "XiaoAi webhook token is not configured"


@pytest.mark.parametrize(
    ("header_value", "expected_status", "expected_detail"),
    [
        (None, 401, "Missing webhook token"),
        ("wrong-token", 401, "Invalid webhook token"),
    ],
)
def test_xiaoai_webhook_rejects_missing_or_invalid_token(
    client,
    monkeypatch,
    header_value,
    expected_status,
    expected_detail,
):
    monkeypatch.setattr(settings, "xiaoai_webhook_token", "expected-token")
    headers = {}
    if header_value is not None:
        headers["X-Webhook-Token"] = header_value

    response = client.post(
        "/api/items/xiaoai/voice/webhook",
        json={"text": "今天放了一袋鸡柳在冷冻室"},
        headers=headers,
    )

    assert response.status_code == expected_status
    assert response.json()["detail"] == expected_detail


def test_xiaoai_webhook_accepts_valid_token(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "xiaoai_webhook_token", "expected-token")

    response = client.post(
        "/api/items/xiaoai/voice/webhook",
        json={"text": "今天放了一袋鸡柳在冷冻室"},
        headers={"X-Webhook-Token": "expected-token"},
    )

    assert response.status_code == 201
    assert response.json() == {"ok": True, "item_id": 1}

    item = db_session.query(FoodItem).one()
    assert item.name == "鸡柳"
    assert item.location == "冷冻室"
    assert item.expiry_date == date.today() + timedelta(days=30)
    assert item.needs_confirmation is True
