from sqlalchemy import create_engine, text

from app.db.session import ensure_sqlite_schema


def test_ensure_sqlite_schema_adds_missing_columns_for_existing_food_items_table(tmp_path):
    database_path = tmp_path / "legacy.db"
    engine = create_engine(
        f"sqlite:///{database_path}",
        connect_args={"check_same_thread": False},
    )

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE food_items (
                    id INTEGER NOT NULL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    location VARCHAR(255) NOT NULL,
                    entry_date DATETIME NOT NULL,
                    expiry_date DATE NOT NULL,
                    status VARCHAR(32) NOT NULL
                )
                """
            )
        )

    ensure_sqlite_schema(engine)

    with engine.connect() as connection:
        columns = connection.execute(text("PRAGMA table_info(food_items)")).fetchall()

    column_names = {column[1] for column in columns}
    assert "needs_confirmation" in column_names
    assert "last_notified_stage" in column_names
