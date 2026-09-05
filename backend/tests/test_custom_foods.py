from tests.test_meals import create_profile
from tests.test_profiles import create_test_client


def test_custom_food_is_private_versioned_and_usable_in_diary() -> None:
    client, _ = create_test_client()
    try:
        owner_headers = create_profile(client)
        other_headers = create_profile(client)
        created = client.post(
            "/v1/custom-foods",
            headers=owner_headers,
            json={
                "name_fa": "غذای خانگی",
                "name_en": "Homemade food",
                "kcal_per_100g": 200,
                "protein_g_per_100g": 10,
                "portion_name_fa": "یک کاسه",
                "portion_grams": 250,
            },
        )

        assert created.status_code == 201
        food = created.json()
        assert food["nutrition_status"] == "user_provided"
        assert food["profile_version"] == 1
        assert client.get("/v1/custom-foods", headers=other_headers).json() == []

        updated = client.patch(
            f"/v1/custom-foods/{food['id']}",
            headers=owner_headers,
            json={"kcal_per_100g": 220},
        )
        assert updated.status_code == 200
        assert updated.json()["profile_version"] == 2

        meal = client.post(
            "/v1/meals",
            headers=owner_headers,
            json={
                "meal_type": "snack",
                "eaten_at": "2026-09-05T15:00:00+00:00",
                "source": "manual",
                "components": [{"food_id": food["id"], "grams": 50}],
            },
        )
        assert meal.status_code == 201
        assert meal.json()["totals"]["kcal"] == 110.0
        assert meal.json()["totals"]["protein_g"] == 5.0

        exported = client.get("/v1/profile/export", headers=owner_headers)
        assert exported.status_code == 200
        exported_food = exported.json()["custom_foods"][0]
        assert len(exported_food["profile_versions"]) == 2
        assert exported_food["profile_versions"][1]["protein_g_per_100g"] == "10.000"
        assert exported_food["portions"][0]["grams"] == "250.00"

        assert client.delete(
            f"/v1/custom-foods/{food['id']}", headers=other_headers
        ).status_code == 404
        assert client.delete(
            f"/v1/custom-foods/{food['id']}", headers=owner_headers
        ).status_code == 204
        assert client.get("/v1/custom-foods", headers=owner_headers).json() == []
        assert client.get(
            f"/v1/meals/{meal.json()['id']}", headers=owner_headers
        ).status_code == 200
        assert client.delete("/v1/profile", headers=owner_headers).status_code == 204
        assert client.get("/v1/profile", headers=owner_headers).status_code == 401
    finally:
        client.app.dependency_overrides.clear()