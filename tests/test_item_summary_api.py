from datetime import date, timedelta

from app.models.food_item import FoodItem


def test_item_summary_api_returns_inventory_counts(client, db_session):
    today = date.today()

    items = [
        {
            "name": "过期苹果",
            "location": "冷藏室",
            "expiry_date": (today - timedelta(days=1)).isoformat(),
        },
        {
            "name": "鲜牛奶",
            "location": "冷藏室",
            "expiry_date": (today + timedelta(days=2)).isoformat(),
        },
        {
            "name": "酸奶",
            "location": "冰箱门架",
            "expiry_date": (today + timedelta(days=7)).isoformat(),
        },
        {
            "name": "面包",
            "location": "常温区",
            "expiry_date": (today + timedelta(days=10)).isoformat(),
        },
        {
            "name": "奶酪",
            "location": "冷藏室",
            "expiry_date": (today + timedelta(days=3)).isoformat(),
        },
    ]

    for item in items:
        response = client.post("/api/items", json=item)
        assert response.status_code == 201

    pending_item = FoodItem(
        name="待确认沙拉",
        location="水果篮",
        expiry_date=today + timedelta(days=5),
        status="active",
        needs_confirmation=True,
    )
    db_session.add(pending_item)
    db_session.add(
        FoodItem(
            name="大米",
            location="冰箱冷冻室",
            expiry_date=today + timedelta(days=30),
            status="discarded",
            needs_confirmation=False,
        )
    )
    db_session.add(
        FoodItem(
            name="果汁",
            location="冰箱冷冻室",
            expiry_date=today - timedelta(days=4),
            status="consumed",
            needs_confirmation=False,
        )
    )
    db_session.commit()

    response = client.get("/api/items/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_count"] == 8
    assert payload["pending_confirmation_count"] == 1
    assert payload["expired_count"] == 2
    assert payload["due_within_3_days_count"] == 2
    assert payload["due_within_7_days_count"] == 4
    assert payload["distinct_location_count"] == 4
    assert payload["location_counts"] == [
        {"location": "冰箱门架", "count": 1},
        {"location": "冷藏室", "count": 3},
        {"location": "常温区", "count": 1},
        {"location": "水果篮", "count": 1},
    ]
