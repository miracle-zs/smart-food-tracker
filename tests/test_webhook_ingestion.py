import pytest

from app.models.food_item import FoodItem


@pytest.mark.parametrize(
    "payload",
    [
        {"text": "今天放了一袋鸡柳在冷冻室"},
        {"raw_text": "今天放了一袋鸡柳在冷冻室"},
        {"query": {"text": "今天放了一袋鸡柳在冷冻室"}},
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
    assert item.needs_confirmation is True
