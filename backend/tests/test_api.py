import io
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_allows_local_flutter_web() -> None:
    response = client.options(
        "/v1/recognition",
        headers={
            "Origin": "http://127.0.0.1:8080",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
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