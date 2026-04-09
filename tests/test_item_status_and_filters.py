def test_status_updates_and_filters(client):
    milk = client.post(
        "/api/items",
        json={
            "name": "鲜牛奶",
            "location": "冷藏室",
            "expiry_date": "2026-04-12",
        },
    ).json()
    chicken = client.post(
        "/api/items",
        json={
            "name": "鸡柳",
            "location": "冰箱冷冻室",
            "expiry_date": "2026-10-31",
        },
    ).json()

    consumed_response = client.put(
        f"/api/items/{milk['id']}/status",
        json={"status": "consumed"},
    )
    discarded_response = client.put(
        f"/api/items/{chicken['id']}/status",
        json={"status": "discarded"},
    )

    assert consumed_response.status_code == 200
    assert discarded_response.status_code == 200

    active_items = client.get("/api/items", params={"status": "active"}).json()
    consumed_items = client.get("/api/items", params={"status": "consumed"}).json()
    freezer_items = client.get("/api/items", params={"location": "冰箱冷冻室"}).json()

    assert active_items == []
    assert [item["name"] for item in consumed_items] == ["鲜牛奶"]
    assert [item["status"] for item in freezer_items] == ["discarded"]


def test_status_update_rejects_unsupported_values(client):
    item = client.post(
        "/api/items",
        json={
            "name": "酸奶",
            "location": "冷藏室",
            "expiry_date": "2026-04-15",
        },
    ).json()

    for unsupported_status in ("active", "archived"):
        response = client.put(
            f"/api/items/{item['id']}/status",
            json={"status": unsupported_status},
        )

        assert response.status_code == 422
