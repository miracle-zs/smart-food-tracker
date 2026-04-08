from datetime import date


def test_edit_active_item_updates_name_location_and_expiry_date(client):
    created_response = client.post(
        "/api/items",
        json={
            "name": "鲜牛奶",
            "location": "冷藏室",
            "expiry_date": "2026-04-12",
        },
    )
    created_item = created_response.json()

    response = client.put(
        f"/api/items/{created_item['id']}",
        json={
            "name": "低脂牛奶",
            "location": "冰箱门架",
            "expiry_date": "2026-04-20",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "低脂牛奶"
    assert payload["location"] == "冰箱门架"
    assert payload["expiry_date"] == "2026-04-20"
    assert payload["status"] == "active"
    assert payload["days_left"] == (date.fromisoformat("2026-04-20") - date.today()).days


def test_confirm_item_clears_needs_confirmation(client):
    voice_response = client.post(
        "/api/items/voice",
        json={
            "raw_text": "放了一盒沙拉",
        },
    )
    voice_item = voice_response.json()["item"]
    assert voice_item["needs_confirmation"] is True

    response = client.post(f"/api/items/{voice_item['id']}/confirm")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == voice_item["id"]
    assert payload["needs_confirmation"] is False


def test_edit_and_confirm_reject_non_active_items(client):
    created_item = client.post(
        "/api/items",
        json={
            "name": "鲜牛奶",
            "location": "冷藏室",
            "expiry_date": "2026-04-12",
        },
    ).json()

    status_response = client.put(
        f"/api/items/{created_item['id']}/status",
        json={"status": "consumed"},
    )
    assert status_response.status_code == 200

    edit_response = client.put(
        f"/api/items/{created_item['id']}",
        json={
            "name": "低脂牛奶",
            "location": "冰箱门架",
            "expiry_date": "2026-04-20",
        },
    )
    assert edit_response.status_code == 409
    assert edit_response.json()["detail"] == "Only active items can be edited"

    confirm_response = client.post(f"/api/items/{created_item['id']}/confirm")
    assert confirm_response.status_code == 409
    assert confirm_response.json()["detail"] == "Only active items can be confirmed"
