import importlib
import json
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable
from sqlalchemy.orm import Session, sessionmaker

from app.db.catalog_seed import build_catalog_seed
from app.db.models import (
    Base,
    Food,
    FoodPortion,
    FoodProfileVersion,
    NutritionSource,
    Profile,
)
from app.main import _database_food_response, _published_foods
from app.nutrition import FOODS


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


def test_catalog_seed_is_complete_and_deterministic() -> None:
    first = build_catalog_seed()
    second = build_catalog_seed()

    assert first == second
    assert len(first.foods) == 87
    assert len(first.profiles) == 87
    assert len(first.portions) == sum(len(food.portions) for food in FOODS)
    assert {row["food_id"] for row in first.profiles} == {
        row["id"] for row in first.foods
    }
    assert all(row["review_state"] == "draft" for row in first.profiles)
    assert all(row["protein_g_per_100g"] is None for row in first.profiles)


def test_catalog_snapshot_matches_current_seed() -> None:
    seed = build_catalog_seed()
    expected = json.loads(
        (Path(__file__).parents[1] / "migrations/data/catalog_v1.json").read_text(
            encoding="utf-8"
        )
    )
    actual = json.loads(
        json.dumps(
            {
                "source": seed.source,
                "foods": seed.foods,
                "profiles": seed.profiles,
                "portions": seed.portions,
            },
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        )
    )

    assert actual == expected


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


def test_production_catalog_returns_only_published_profiles() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def register_char_length(connection, _record) -> None:
        connection.create_function(
            "char_length", 1, lambda value: len(value) if value is not None else None
        )

    Base.metadata.create_all(engine)
    now = datetime(2026, 9, 5, tzinfo=UTC)
    with Session(engine) as session:
        source = NutritionSource(
            name="Public nutrition source",
            source_type="government_db",
            publication_id="test-release",
            accessed_at=date(2026, 9, 5),
            licence_note="Public test fixture",
        )
        session.add(source)
        for food_id, review_state in (
            ("published-food", "source_checked"),
            ("draft-food", "draft"),
        ):
            session.add(
                Food(
                    id=food_id,
                    name_fa=food_id,
                    name_en=food_id,
                    family="test",
                    is_canonical=True,
                    created_at=now,
                )
            )
            session.flush()
            session.add_all(
                [
                    FoodProfileVersion(
                        food_id=food_id,
                        version=1,
                        source_id=source.id,
                        review_state=review_state,
                        kcal_per_100g=Decimal("120"),
                        protein_g_per_100g=Decimal("8.2"),
                        carb_g_per_100g=Decimal("7.1"),
                        fat_g_per_100g=Decimal("6.5"),
                        fiber_g_per_100g=Decimal("2.4"),
                        uncertainty_percent=Decimal("10"),
                        effective_at=now,
                    ),
                    FoodPortion(
                        food_id=food_id,
                        code="100g",
                        name_fa="100 g",
                        grams=Decimal("100"),
                        is_default=True,
                        source_id=source.id,
                    ),
                ]
            )
        session.commit()

        published = _published_foods(session)
        response = _database_food_response(*published[0])

    assert [food.id for food, _, _ in published] == ["published-food"]
    assert response.nutrition_status == "source_checked"
    assert response.protein_g_per_100g == 8.2


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