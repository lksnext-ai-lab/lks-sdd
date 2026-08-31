from __future__ import annotations

from uuid import uuid4

from sqlalchemy import Engine, create_engine, text


def create_database_engine(database_url: str) -> Engine:
    return create_engine(database_url, pool_pre_ping=True, pool_recycle=300)


def ensure_items(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE IF NOT EXISTS reference_items ("
                "id varchar(36) PRIMARY KEY, label varchar(200) NOT NULL)"
            )
        )


def create_item(engine: Engine, label: str) -> dict[str, str]:
    item = {"id": str(uuid4()), "label": label}
    with engine.begin() as connection:
        connection.execute(
            text("INSERT INTO reference_items (id, label) VALUES (:id, :label)"),
            item,
        )
    return item


def list_items(engine: Engine) -> list[dict[str, str]]:
    with engine.connect() as connection:
        rows = connection.execute(
            text("SELECT id, label FROM reference_items ORDER BY label, id")
        )
        return [{"id": str(row.id), "label": str(row.label)} for row in rows]
