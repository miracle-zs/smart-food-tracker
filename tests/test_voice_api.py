from datetime import date, timedelta


def test_voice_ingestion_falls_back_to_30_days_and_marks_confirmation(client):
    response = client.post(
        "/api/items/voice",
        json={"raw_text": "今天放了一袋鸡柳在冷冻室"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["item"]["name"] == "鸡柳"
    assert payload["item"]["location"] == "冷冻室"
    assert payload["item"]["needs_confirmation"] is True
    assert payload["item"]["expiry_date"] == (date.today() + timedelta(days=30)).isoformat()


def test_voice_ingestion_keeps_explicit_date_and_location(client):
    response = client.post(
        "/api/items/voice",
        json={"raw_text": "今天放了一袋鸡柳在冷冻室，2026-10-31过期"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["item"]["location"] == "冷冻室"
    assert payload["item"]["expiry_date"] == "2026-10-31"
    assert payload["item"]["needs_confirmation"] is False
