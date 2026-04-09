from datetime import date, datetime, timezone

from app.models.food_item import FoodItem


def _add_item(db_session, *, name, location, expiry_date, entry_date, status="active"):
    item = FoodItem(
        name=name,
        location=location,
        expiry_date=expiry_date,
        entry_date=entry_date,
        status=status,
    )
    db_session.add(item)
    db_session.commit()
    return item


def test_item_querying_supports_search_filters_and_sorting(client, db_session):
    _add_item(
        db_session,
        name="Whole Milk",
        location="Cold Fridge",
        expiry_date=date(2026, 4, 12),
        entry_date=datetime(2026, 4, 1, 8, 0, tzinfo=timezone.utc),
    )
    _add_item(
        db_session,
        name="Chocolate Milk",
        location="Cold Fridge",
        expiry_date=date(2026, 4, 18),
        entry_date=datetime(2026, 4, 2, 8, 0, tzinfo=timezone.utc),
        status="consumed",
    )
    _add_item(
        db_session,
        name="Greek Yogurt",
        location="Fresh Freezer",
        expiry_date=date(2026, 4, 10),
        entry_date=datetime(2026, 4, 3, 8, 0, tzinfo=timezone.utc),
    )
    _add_item(
        db_session,
        name="Paper Towels",
        location="Pantry",
        expiry_date=date(2026, 4, 20),
        entry_date=datetime(2026, 4, 4, 8, 0, tzinfo=timezone.utc),
    )

    name_search = client.get("/api/items?q=milk")
    assert name_search.status_code == 200
    assert [item["name"] for item in name_search.json()] == ["Whole Milk", "Chocolate Milk"]

    location_search = client.get("/api/items?q=freezer")
    assert location_search.status_code == 200
    assert [item["name"] for item in location_search.json()] == ["Greek Yogurt"]

    status_filtered_search = client.get("/api/items?q=milk&status=active")
    assert status_filtered_search.status_code == 200
    assert [item["name"] for item in status_filtered_search.json()] == ["Whole Milk"]

    location_filtered_search = client.get("/api/items?q=freezer&location=Pantry")
    assert location_filtered_search.status_code == 200
    assert location_filtered_search.json() == []

    default_sorted = client.get("/api/items")
    assert default_sorted.status_code == 200
    assert [item["name"] for item in default_sorted.json()] == [
        "Greek Yogurt",
        "Whole Milk",
        "Chocolate Milk",
        "Paper Towels",
    ]

    expiry_asc_sorted = client.get("/api/items?sort=expiry_date_asc")
    assert expiry_asc_sorted.status_code == 200
    assert [item["name"] for item in expiry_asc_sorted.json()] == [
        "Greek Yogurt",
        "Whole Milk",
        "Chocolate Milk",
        "Paper Towels",
    ]

    expiry_desc_sorted = client.get("/api/items?sort=expiry_date_desc")
    assert expiry_desc_sorted.status_code == 200
    assert [item["name"] for item in expiry_desc_sorted.json()] == [
        "Paper Towels",
        "Chocolate Milk",
        "Whole Milk",
        "Greek Yogurt",
    ]

    entry_desc_sorted = client.get("/api/items?sort=entry_date_desc")
    assert entry_desc_sorted.status_code == 200
    assert [item["name"] for item in entry_desc_sorted.json()] == [
        "Paper Towels",
        "Greek Yogurt",
        "Chocolate Milk",
        "Whole Milk",
    ]

    invalid_sort_sorted = client.get("/api/items?sort=not-a-real-sort")
    assert invalid_sort_sorted.status_code == 200
    assert [item["name"] for item in invalid_sort_sorted.json()] == [
        "Greek Yogurt",
        "Whole Milk",
        "Chocolate Milk",
        "Paper Towels",
    ]
