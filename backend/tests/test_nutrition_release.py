import json
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session

from app.db.models import Base, Food, FoodProfileVersion
from app.domain.nutrition_release import apply_release, load_release


def release_data() -> dict[str, object]:
    return {
        "release_id": "test-release",
        "source": {
            "name": "Licensed test source",
            "source_type": "government_db",
            "publication_id": "fixture-1",
            "accessed_at": "2026-09-05",
            "licence_note": "Test fixture only",
        },
        "review_state": "source_checked",
        "reviewer_note": "Source values checked against fixture-1.",
        "effective_at": "2026-09-05T00:00:00Z",
        "foods": [
            {
                "food_id": "test-food",
                "kcal_per_100g": 120,
                "protein_g_per_100g": 8.2,
                "carb_g_per_100g": 7.1,
                "fat_g_per_100g": 6.5,
                "fiber_g_per_100g": 2.4,
                "uncertainty_percent": 10,
            }
        ],
    }


def test_release_requires_expected_count_and_complete_source(tmp_path) -> None:
    path = tmp_path / "release.json"
    path.write_text(json.dumps(release_data()), encoding="utf-8")

    release = load_release(path, expected_count=1)
    assert release.foods[0].protein_g_per_100g == Decimal("8.2")
    with pytest.raises(ValueError, match="exactly 20"):
        load_release(path)

    data = release_data()
    data["source"]["reference_url"] = "http://example.invalid/source"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="HTTPS"):
        load_release(path, expected_count=1)


def test_release_is_applied_as_a_new_published_version(tmp_path) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def register_char_length(connection, _record) -> None:
        connection.create_function(
            "char_length", 1, lambda value: len(value) if value is not None else None
        )

    Base.metadata.create_all(engine)
    path = tmp_path / "release.json"
    path.write_text(json.dumps(release_data()), encoding="utf-8")
    release = load_release(path, expected_count=1)
    with Session(engine) as session:
        session.add(
            Food(
                id="test-food",
                name_fa="test",
                name_en="test",
                family="test",
                is_canonical=True,
                created_at=datetime(2026, 9, 5, tzinfo=UTC),
            )
        )
        session.commit()
        assert apply_release(session, release) == 1
        session.commit()
        assert apply_release(session, release) == 1
        session.commit()
        versions = list(
            session.scalars(
                select(FoodProfileVersion).order_by(FoodProfileVersion.version)
            ).all()
        )

    assert [version.version for version in versions] == [1, 2]
    assert versions[0].retired_at is not None
    assert versions[1].retired_at is None
    assert versions[1].review_state == "source_checked"
    assert versions[1].reviewer_note == "Source values checked against fixture-1."
    assert versions[1].protein_g_per_100g == Decimal("8.200")