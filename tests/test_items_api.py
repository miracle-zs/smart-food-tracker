from datetime import date


def test_create_item_and_list_items_sorted_by_expiry(client):
    later_response = client.post(
        "/api/items",
        json={
            "name": "鸡柳",
            "location": "冰箱冷冻室",
            "expiry_date": "2026-10-31",
        },
    )
    assert later_response.status_code == 201

    earlier_response = client.post(
        "/api/items",
        json={
            "name": "鲜牛奶",
            "location": "冷藏室",
            "expiry_date": "2026-04-12",
        },
    )
    assert earlier_response.status_code == 201

    list_response = client.get("/api/items")

    assert list_response.status_code == 200
    payload = list_response.json()
    assert [item["name"] for item in payload] == ["鲜牛奶", "鸡柳"]
    assert payload[0]["location"] == "冷藏室"
    assert payload[0]["status"] == "active"
    assert payload[0]["days_left"] == (date.fromisoformat("2026-04-12") - date.today()).days
    assert payload[0]["urgency"] in {"safe", "warning", "critical", "expired"}
