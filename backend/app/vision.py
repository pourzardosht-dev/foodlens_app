import base64
import io
import os
from abc import ABC, abstractmethod

import httpx
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field

from app.nutrition import FOODS


MAX_IMAGE_BYTES = 8 * 1024 * 1024
SUPPORTED_IMAGE_FORMATS = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}


class VisionError(RuntimeError):
    pass


class InvalidImageError(ValueError):
    pass


class FoodCandidate(BaseModel):
    food_id: str
    confidence: float = Field(ge=0, le=1)


class RecognitionResult(BaseModel):
    food_id: str | None
    confidence: float = Field(ge=0, le=1)
    is_food: bool
    needs_confirmation: bool
    alternatives: list[FoodCandidate] = Field(default_factory=list, max_length=3)


class ValidatedImage(BaseModel):
    content: bytes
    mime_type: str


GEMINI_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "food_id": {"type": "string", "nullable": True},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "is_food": {"type": "boolean"},
        "needs_confirmation": {"type": "boolean"},
        "alternatives": {
            "type": "array",
            "maxItems": 3,
            "items": {
                "type": "object",
                "properties": {
                    "food_id": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                },
                "required": ["food_id", "confidence"],
            },
        },
    },
    "required": [
        "food_id",
        "confidence",
        "is_food",
        "needs_confirmation",
        "alternatives",
    ],
}


def validate_image(content: bytes) -> ValidatedImage:
    if not content:
        raise InvalidImageError("Image is empty")
    if len(content) > MAX_IMAGE_BYTES:
        raise InvalidImageError("Image exceeds the 8 MB limit")

    try:
        with Image.open(io.BytesIO(content)) as image:
            image.verify()
            detected_format = image.format
    except (UnidentifiedImageError, OSError) as error:
        raise InvalidImageError("File is not a valid image") from error

    if detected_format == "AVIF":
        normalized = io.BytesIO()
        with Image.open(io.BytesIO(content)) as image:
            image.convert("RGB").save(normalized, format="JPEG", quality=90)
        return ValidatedImage(content=normalized.getvalue(), mime_type="image/jpeg")

    mime_type = SUPPORTED_IMAGE_FORMATS.get(detected_format or "")
    if mime_type is None:
        raise InvalidImageError("Only JPEG, PNG, WebP and AVIF images are supported")
    return ValidatedImage(content=content, mime_type=mime_type)


class VisionProvider(ABC):
    @abstractmethod
    async def recognize(self, image: ValidatedImage) -> RecognitionResult:
        raise NotImplementedError


class MockVisionProvider(VisionProvider):
    async def recognize(self, image: ValidatedImage) -> RecognitionResult:
        return RecognitionResult(
            food_id=None,
            confidence=0,
            is_food=True,
            needs_confirmation=True,
        )


def build_recognition_prompt() -> str:
    food_catalog = "; ".join(
        f"{food.id}: {food.name_fa} ({food.name_en}) - {food.recognition_hints}"
        for food in FOODS
    )
    return (
        "Classify the main Iranian food in this image. Only choose from this catalog: "
        f"{food_catalog}. Return null food_id when the image is not food, is outside the "
        "catalog, or is too ambiguous. Compare the visual evidence against the catalog "
        "hints, especially for similar stews; do not choose the closest-looking item when "
        "its defining ingredients are absent. Confidence must reflect uncertainty; set "
        "needs_confirmation=true below 0.85. Do not estimate calories or portion."
    )


class GeminiVisionProvider(VisionProvider):
    def __init__(self, api_key: str, model: str = "gemini-3.6-flash") -> None:
        if not api_key:
            raise VisionError("GEMINI_API_KEY is required")
        self._api_key = api_key
        self._model = model

    async def recognize(self, image: ValidatedImage) -> RecognitionResult:
        prompt = build_recognition_prompt()
        request = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt},
                        {
                            "inlineData": {
                                "mimeType": image.mime_type,
                                "data": base64.b64encode(image.content).decode("ascii"),
                            }
                        },
                    ],
                }
            ],
            "generationConfig": {
                "temperature": 0,
                "responseMimeType": "application/json",
                "responseSchema": GEMINI_RESPONSE_SCHEMA,
            },
        }
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}:"
            "generateContent"
        )
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    url,
                    json=request,
                    headers={"x-goog-api-key": self._api_key},
                )
                response.raise_for_status()
            text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            result = RecognitionResult.model_validate_json(text)
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as error:
            raise VisionError("Gemini recognition failed") from error

        allowed_ids = {food.id for food in FOODS}
        if result.food_id is not None and result.food_id not in allowed_ids:
            raise VisionError("Gemini returned an unsupported food id")
        if any(item.food_id not in allowed_ids for item in result.alternatives):
            raise VisionError("Gemini returned an unsupported alternative")
        return result


def create_vision_provider() -> VisionProvider:
    provider = os.getenv("VISION_PROVIDER", "mock").lower()
    if provider == "mock":
        return MockVisionProvider()
    if provider == "gemini":
        return GeminiVisionProvider(
            api_key=os.getenv("GEMINI_API_KEY", ""),
            model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
        )
    raise VisionError(f"Unsupported VISION_PROVIDER: {provider}")