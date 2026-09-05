from sqlalchemy import insert

from app.db.catalog_seed import build_catalog_seed
from app.db.models import Food, FoodPortion, FoodProfileVersion, NutritionSource
from tests.test_profiles import create_test_client


def create_profile(client) -> dict[str, str]:
    response = client.post("/v1/profiles/anonymous", json={"timezone": "UTC"})
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['token']}"}


def seed_catalog(session_factory) -> None:
    seed = build_catalog_seed()
    with session_factory() as session:
        session.execute(insert(NutritionSource), [seed.source])
        session.execute(insert(Food), list(seed.foods))
        session.execute(insert(FoodProfileVersion), list(seed.profiles))
        session.execute(insert(FoodPortion), list(seed.portions))
        session.commit()


def test_meal_crud_snapshots_and_profile_isolation() -> None:
    client, session_factory = create_test_client()
    try:
        seed_catalog(session_factory)
        first_headers = create_profile(client)
        second_headers = create_profile(client)

        created = client.post(
            "/v1/meals",
            headers=first_headers,
            json={
                "meal_type": "lunch",
                "eaten_at": "2026-09-05T13:15:00+00:00",
                "source": "photo",
                "components": [
                    {
                        "food_id": "cooked-rice",
                        "grams": 250,
                        "recognition_confidence": 0.92,
                    },
                    {
                        "food_id": "ghormeh-sabzi",
                        "grams": 180,
                        "recognition_confidence": 0.88,
                    },
                ],
            },
        )

        assert created.status_code == 201
        meal = created.json()
        assert [item["food_id"] for item in meal["components"]] == [
            "cooked-rice",
            "ghormeh-sabzi",
        ]
        assert meal["components"][1]["food_name_fa"] == "قرمه‌سبزی"
        assert meal["totals"]["kcal"] == 622.0
        assert meal["totals"]["protein_g"] is None
        assert meal["completeness_percent"]["protein_g"] == 0

        meal_id = meal["id"]
        other_user = client.get(f"/v1/meals/{meal_id}", headers=second_headers)
        assert other_user.status_code == 404

        day = client.get(
            "/v1/diary/day?date=2026-09-05", headers=first_headers
        )
        assert day.status_code == 200
        assert day.json()["totals"]["kcal"] == 622.0
        assert len(day.json()["meals"]) == 1
        exported = client.get("/v1/profile/export", headers=first_headers)
        assert exported.status_code == 200
        assert len(exported.json()["meals"][0]["components"]) == 2

        updated = client.patch(
            f"/v1/meals/{meal_id}",
            headers=first_headers,
            json={
                "meal_type": "dinner",
                "components": [{"food_id": "cooked-rice", "grams": 100}],
            },
        )
        assert updated.status_code == 200
        assert updated.json()["meal_type"] == "dinner"
        assert updated.json()["totals"]["kcal"] == 130.0

        added = client.post(
            f"/v1/meals/{meal_id}/components",
            headers=first_headers,
            json={"food_id": "ghormeh-sabzi", "grams": 100},
        )
        assert added.status_code == 201
        assert [item["position"] for item in added.json()["components"]] == [0, 1]

        second_component = added.json()["components"][1]
        changed = client.patch(
            f"/v1/meals/{meal_id}/components/{second_component['id']}",
            headers=first_headers,
            json={"food_id": "ghormeh-sabzi", "grams": 200},
        )
        assert changed.status_code == 200
        assert changed.json()["totals"]["kcal"] == 460.0

        removed = client.delete(
            f"/v1/meals/{meal_id}/components/{second_component['id']}",
            headers=first_headers,
        )
        assert removed.status_code == 204

        deleted = client.delete(f"/v1/meals/{meal_id}", headers=first_headers)
        assert deleted.status_code == 204
        assert client.get(
            f"/v1/meals/{meal_id}", headers=first_headers
        ).status_code == 404
    finally:
        client.app.dependency_overrides.clear()
