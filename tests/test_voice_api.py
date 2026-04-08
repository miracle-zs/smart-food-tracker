from datetime import date, timedelta

import pytest


CURRENT_YEAR = date.today().year


def test_voice_ingestion_falls_back_to_30_days_and_marks_confirmation(client):
    response = client.post(
        "/api/items/voice",
        json={"raw_text": "放了一袋鸡柳在冷冻室"},
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


def test_voice_ingestion_invalid_explicit_iso_date_falls_back_safely(client):
    response = client.post(
        "/api/items/voice",
        json={"raw_text": "2026-02-31过期"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["item"]["expiry_date"] == (date.today() + timedelta(days=30)).isoformat()
    assert payload["item"]["needs_confirmation"] is True


@pytest.mark.parametrize(
    ("raw_text", "expected_date", "expected_needs_confirmation"),
    [
        ("今年10月底过期", date(CURRENT_YEAR, 10, 31).isoformat(), False),
        ("10月31日过期", date(CURRENT_YEAR, 10, 31).isoformat(), False),
        ("3天后过期", (date.today() + timedelta(days=3)).isoformat(), False),
        ("明天过期", (date.today() + timedelta(days=1)).isoformat(), False),
    ],
)
def test_voice_ingestion_parses_relative_and_local_dates(client, raw_text, expected_date, expected_needs_confirmation):
    response = client.post(
        "/api/items/voice",
        json={"raw_text": raw_text},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["item"]["expiry_date"] == expected_date
    assert payload["item"]["needs_confirmation"] is expected_needs_confirmation


@pytest.mark.parametrize(
    ("raw_text", "expected_date", "expected_needs_confirmation"),
    [
        (
            "2026-04-01买的牛奶明天过期",
            (date.today() + timedelta(days=1)).isoformat(),
            False,
        ),
        ("今天放了一袋鸡柳在冷冻室，10月31日过期", date(CURRENT_YEAR, 10, 31).isoformat(), False),
        ("今天买的牛奶明天过期", (date.today() + timedelta(days=1)).isoformat(), False),
        ("13月底过期", (date.today() + timedelta(days=30)).isoformat(), True),
        ("13月31日过期", (date.today() + timedelta(days=30)).isoformat(), True),
        ("2月31日过期", (date.today() + timedelta(days=30)).isoformat(), True),
        ("11月31日过期", (date.today() + timedelta(days=30)).isoformat(), True),
    ],
)
def test_voice_ingestion_scopes_relative_dates_and_handles_invalid_months(
    client,
    raw_text,
    expected_date,
    expected_needs_confirmation,
):
    response = client.post(
        "/api/items/voice",
        json={"raw_text": raw_text},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["item"]["expiry_date"] == expected_date
    assert payload["item"]["needs_confirmation"] is expected_needs_confirmation
