import io
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.nutrition import FOODS, RECOGNITION_FAMILIES
from app.vision import GEMINI_RESPONSE_SCHEMA, build_recognition_prompt


client = TestClient(app)


def test_gemini_schema_does_not_use_unsupported_references() -> None:
    schema_text = str(GEMINI_RESPONSE_SCHEMA)

    assert "$defs" not in schema_text
    assert "$ref" not in schema_text


def test_food_catalog_includes_similar_gilaki_stews() -> None:
    foods_response = client.get("/v1/foods")

    assert foods_response.status_code == 200
    foods_by_id = {food["id"]: food for food in foods_response.json()}
    assert foods_by_id["baghala-ghatogh"]["name_fa"] == "باقلاقاتق"
    assert foods_by_id["anarbij"]["name_fa"] == "اناربیج"


def test_food_catalog_contains_87_complete_profiles() -> None:
    response = client.get("/v1/foods")

    assert response.status_code == 200
    foods = response.json()
    assert len(foods) == 87
    assert {food["id"] for food in foods} == {
        "abgoosht",
        "adas-polo",
        "adasi",
        "albaloo-polo",
        "anarbij",
        "apple",
        "ash-doogh",
        "ash-reshteh",
        "baghala-ghatogh",
        "baghali-polo-goosht",
        "banana",
        "bandari-sandwich",
        "biscuit",
        "bread-tahdig",
        "cheeseburger",
        "chicken-sandwich",
        "chocolate",
        "cola",
        "cooked-rice",
        "cream-pastry",
        "dates",
        "diet-cola",
        "dolmeh-barg-mo",
        "doogh",
        "dry-pastry",
        "estamboli-polo",
        "falafel-sandwich",
        "fesenjan",
        "french-fries",
        "fried-chicken",
        "ghalieh-mahi",
        "gheimeh",
        "gheimeh-bademjan",
        "ghormeh-sabzi",
        "grapes",
        "halim",
        "hamburger",
        "hot-dog",
        "iranian-macaroni",
        "joojeh-kebab",
        "kabab-bakhtiari",
        "kabab-barg",
        "kabab-tabei",
        "kabab-torsh",
        "kalam-polo-shirazi",
        "kashk-bademjan",
        "khoresh-aloo-esfenaj",
        "khoresh-bademjan",
        "khoresh-bamieh",
        "khoresh-karafs",
        "koobideh-kebab",
        "kookoo-sabzi",
        "koofteh-tabrizi",
        "kotlet",
        "loobia-polo",
        "lemonade",
        "mahi-shekam-por",
        "margherita-pizza",
        "malt-beverage",
        "melon",
        "meygoo-polo",
        "milk",
        "mirza-ghasemi",
        "mixed-nuts",
        "morgh-torsh",
        "olivieh-sandwich",
        "orange",
        "orange-soda",
        "pepperoni-pizza",
        "pistachios",
        "plain-cake",
        "plain-yogurt",
        "potato-chips",
        "potato-tahdig",
        "reshteh-polo",
        "rice-tahdig",
        "saffron-rice",
        "salad-shirazi",
        "sabzi-polo-mahi",
        "shishlik",
        "tahchin-morgh",
        "tangerine",
        "torsh-tareh",
        "tuna-sandwich",
        "vavishka",
        "watermelon",
        "zereshk-polo-morgh",
    }
    for food in foods:
        assert food["kcal_per_100g"] > 0
        assert 0 < food["uncertainty_percent"] < 100
        portion_ids = {portion["id"] for portion in food["portions"]}
        assert food["default_portion_id"] in portion_ids


def test_recognition_families_cover_catalog_once() -> None:
    food_ids = {food.id for food in FOODS}
    grouped_ids = [
        food_id
        for family_food_ids in RECOGNITION_FAMILIES.values()
        for food_id in family_food_ids
    ]

    assert set(grouped_ids) == food_ids
    assert len(grouped_ids) == len(set(grouped_ids))


def test_recognition_prompt_distinguishes_similar_gilaki_stews() -> None:
    prompt = build_recognition_prompt()

    assert "baghala-ghatogh" in prompt
    assert "broad-bean" in prompt
    assert "visible whole eggs" in prompt
    assert "anarbij" in prompt
    assert "walnut, pomegranate" in prompt
    assert "small meatballs" in prompt
    assert "do not choose the closest-looking item" in prompt


def test_recognition_prompt_groups_similar_foods_by_family() -> None:
    prompt = build_recognition_prompt()

    assert "[stews]" in prompt
    assert "[rice dishes]" in prompt
    assert "[kebabs]" in prompt
    assert "[side dishes]" in prompt
    assert "[fast food]" in prompt
    assert "[sandwiches]" in prompt
    assert "[fruits]" in prompt
    assert "[snacks and sweets]" in prompt
    assert "[nuts]" in prompt
    assert "[drinks and dairy]" in prompt
    assert "identify each component's likely family" in prompt
    assert prompt.index("[stews]") < prompt.index("[rice dishes]")
    assert "alternating chunks of saffron chicken and red meat" in prompt
    assert "cherries are larger and juicier than barberries" in prompt
    assert "khoresh-bamieh" in prompt
    assert "whole green okra pods" in prompt
    assert "every distinct visible food component" in prompt
    assert "estimated_grams" in prompt
    assert "Omit unsupported side dishes" in prompt
    assert "without a visible cheese slice" in prompt
    assert "clearly visible melted yellow cheese" in prompt
    assert "not thick French fries" in prompt
    assert "not round potato tahdig slices" in prompt
    assert "never identify from the dark liquid alone" in prompt
    assert "Non-Alcoholic Malt Beverage" in prompt
    assert "not orange soda" in prompt


def test_gemini_schema_requires_independent_food_components() -> None:
    components = GEMINI_RESPONSE_SCHEMA["properties"]["components"]

    assert components["maxItems"] == 8
    assert components["items"]["required"] == [
        "food_id",
        "confidence",
        "estimated_grams",
    ]


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_database_health_fails_without_affecting_api(monkeypatch) -> None:
    def missing_database():
        raise RuntimeError("DATABASE_URL is required")

    monkeypatch.setattr("app.main.get_engine", missing_database)

    database_response = client.get("/health/database")
    api_response = client.get("/health")

    assert database_response.status_code == 503
    assert database_response.json() == {"status": "not_configured"}
    assert api_response.status_code == 200


def test_cors_allows_local_flutter_web() -> None:
    response = client.options(
        "/v1/recognition",
        headers={
            "Origin": "http://127.0.0.1:8080",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:8080"


def test_estimates_ghormeh_sabzi_ladles() -> None:
    response = client.post(
        "/v1/nutrition/estimate",
        json={
            "food_id": "ghormeh-sabzi",
            "portion_id": "ladle",
            "quantity": 1.5,
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert result["estimated_grams"] == 270.0
    assert result["estimated_calories"] == 445.5
    assert result["calorie_range_min"] == 365.3
    assert result["calorie_range_max"] == 525.7


def test_rejects_portion_from_another_food() -> None:
    response = client.post(
        "/v1/nutrition/estimate",
        json={
            "food_id": "koobideh-kebab",
            "portion_id": "ladle",
            "quantity": 1,
        },
    )

    assert response.status_code == 422


def test_recognition_accepts_valid_jpeg_with_mock_provider(monkeypatch) -> None:
    monkeypatch.setenv("VISION_PROVIDER", "mock")
    image_buffer = io.BytesIO()
    Image.new("RGB", (32, 32), color="green").save(image_buffer, format="JPEG")

    response = client.post(
        "/v1/recognition",
        files={"image": ("food.jpg", image_buffer.getvalue(), "image/jpeg")},
    )

    assert response.status_code == 200
    assert response.json() == {
        "food_id": None,
        "confidence": 0.0,
        "is_food": True,
        "needs_confirmation": True,
        "alternatives": [],
        "components": [],
    }


def test_recognition_rejects_non_image() -> None:
    response = client.post(
        "/v1/recognition",
        files={"image": ("not-food.txt", b"not an image", "text/plain")},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "File is not a valid image"


def test_recognition_normalizes_avif_from_gold_dataset(monkeypatch) -> None:
    monkeypatch.setenv("VISION_PROVIDER", "mock")
    image_path = (
        Path(__file__).parents[2] / "food pic" / "فسنجان" / "fesenjan171.avif"
    )

    response = client.post(
        "/v1/recognition",
        files={"image": (image_path.name, image_path.read_bytes(), "image/avif")},
    )

    assert response.status_code == 200