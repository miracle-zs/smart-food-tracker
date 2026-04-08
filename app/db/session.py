from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app.config import settings


engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def ensure_sqlite_schema(db_engine: Engine) -> None:
    if db_engine.dialect.name != "sqlite":
        return

    inspector = inspect(db_engine)
    table_names = inspector.get_table_names()
    if "food_items" not in table_names:
        return

    existing_columns = {column["name"] for column in inspector.get_columns("food_items")}
    alter_statements: list[str] = []

    if "needs_confirmation" not in existing_columns:
        alter_statements.append(
            "ALTER TABLE food_items ADD COLUMN needs_confirmation BOOLEAN NOT NULL DEFAULT 0"
        )
    if "last_notified_stage" not in existing_columns:
        alter_statements.append(
            "ALTER TABLE food_items ADD COLUMN last_notified_stage VARCHAR(8)"
        )

    if not alter_statements:
        return

    with db_engine.begin() as connection:
        for statement in alter_statements:
            connection.execute(text(statement))
