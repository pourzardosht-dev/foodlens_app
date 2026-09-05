import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import Meal, Profile
from app.db.session import get_engine
from app.main import app


pytestmark = pytest.mark.postgres


def test_migrated_postgres_profile_diary_and_deletion() -> None:
    if not os.getenv("TEST_DATABASE_URL"):
        pytest.skip("TEST_DATABASE_URL is required for PostgreSQL integration tests")

    client = TestClient(app)
    assert client.get("/health/database").status_code == 200
    assert client.get("/v1/foods").json() == []

    profile_response = client.post(
        "/v1/profiles/anonymous", json={"timezone": "Asia/Tehran"}
    )
    assert profile_response.status_code == 201
    profile_id = uuid.UUID(profile_response.json()["id"])
    headers = {
        "Authorization": f"Bearer {profile_response.json()['token']}"
    }
    meal = client.post(
        "/v1/meals",
        headers=headers,
        json={
            "meal_type": "lunch",
            "eaten_at": "2026-09-05T13:15:00+03:30",
            "source": "manual",
            "components": [{"food_id": "cooked-rice", "grams": 250}],
        },
    )
    assert meal.status_code == 201
    assert meal.json()["totals"]["kcal"] == 325.0
    diary = client.get("/v1/diary/day?date=2026-09-05", headers=headers)
    assert diary.status_code == 200
    assert len(diary.json()["meals"]) == 1
    assert client.delete("/v1/profile", headers=headers).status_code == 204

    with get_engine().connect() as connection:
        assert connection.scalar(select(Profile.id).where(Profile.id == profile_id)) is None
        assert connection.scalar(select(Meal.id).where(Meal.profile_id == profile_id)) is None