import importlib
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import Base, Profile


EXPECTED_TABLES = {
    "profiles",
    "profile_tokens",
    "foods",
    "food_aliases",
    "nutrition_sources",
    "food_profile_versions",
    "food_portions",
    "meals",
    "meal_components",
}


def test_schema_contains_all_v1_tables_and_compiles_for_postgresql() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES

    dialect = postgresql.dialect()
    for table in Base.metadata.sorted_tables:
        assert str(CreateTable(table).compile(dialect=dialect))
        for index in table.indexes:
            assert str(CreateIndex(index).compile(dialect=dialect))


def test_postgresql_identifiers_fit_server_limit() -> None:
    names = {
        item.name
        for table in Base.metadata.tables.values()
        for item in (*table.constraints, *table.indexes)
        if item.name is not None
    }

    assert all(len(name) <= 63 for name in names)


def test_session_scope_commits_and_rolls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    db_session = importlib.import_module("app.db.session")
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.tables["profiles"].create(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr(db_session, "get_session_factory", lambda: session_factory)
    timestamp = datetime(2026, 9, 5, tzinfo=UTC)

    with db_session.session_scope() as session:
        session.add(
            Profile(
                timezone="Asia/Tehran",
                locale="fa-IR",
                created_at=timestamp,
                updated_at=timestamp,
            )
        )

    with Session(engine) as session:
        assert len(session.scalars(select(Profile)).all()) == 1

    with pytest.raises(RuntimeError, match="rollback"):
        with db_session.session_scope() as session:
            session.add(
                Profile(
                    timezone="UTC",
                    locale="en",
                    created_at=timestamp,
                    updated_at=timestamp,
                )
            )
            raise RuntimeError("rollback")

    with Session(engine) as session:
        assert len(session.scalars(select(Profile)).all()) == 1