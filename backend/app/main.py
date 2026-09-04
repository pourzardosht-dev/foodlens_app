import os

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.nutrition import FOODS, estimate_calories, get_food
from app.vision import (
    InvalidImageError,
    RecognitionResult,
    VisionError,
    create_vision_provider,
    validate_image,
)


class PortionResponse(BaseModel):
    id: str
    name_fa: str
    grams: float


class FoodResponse(BaseModel):
    id: str
    name_fa: str
    name_en: str
    kcal_per_100g: float
    uncertainty_percent: float
    default_portion_id: str
    portions: list[PortionResponse]


class EstimateRequest(BaseModel):
    food_id: str
    portion_id: str
    quantity: float = Field(gt=0, le=20)


class EstimateResponse(BaseModel):
    food_id: str
    food_name_fa: str
    portion_name_fa: str
    quantity: float
    estimated_grams: float
    estimated_calories: float
    calorie_range_min: float
    calorie_range_max: float
    confidence: str


app = FastAPI(title="FoodLens API", version="0.1.0")
cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://127.0.0.1:8080,http://localhost:8080",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/foods", response_model=list[FoodResponse])
def list_foods() -> list[FoodResponse]:
    return [
        FoodResponse(
            id=food.id,
            name_fa=food.name_fa,
            name_en=food.name_en,
            kcal_per_100g=food.kcal_per_100g,
            uncertainty_percent=food.uncertainty_percent,
            default_portion_id=food.default_portion_id,
            portions=[
                PortionResponse(id=portion.id, name_fa=portion.name_fa, grams=portion.grams)
                for portion in food.portions
            ],
        )
        for food in FOODS
    ]


@app.post("/v1/recognition", response_model=RecognitionResult)
async def recognize_food(image: UploadFile = File(...)) -> RecognitionResult:
    try:
        validated_image = validate_image(await image.read())
        provider = create_vision_provider()
        return await provider.recognize(validated_image)
    except InvalidImageError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except VisionError as error:
        raise HTTPException(status_code=502, detail="Vision provider unavailable") from error


@app.post("/v1/nutrition/estimate", response_model=EstimateResponse)
def create_estimate(request: EstimateRequest) -> EstimateResponse:
    try:
        food = get_food(request.food_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Food not found") from error

    portion = next(
        (item for item in food.portions if item.id == request.portion_id), None
    )
    if portion is None:
        raise HTTPException(status_code=422, detail="Portion is not valid for this food")

    grams, calories, range_min, range_max = estimate_calories(
        food, portion, request.quantity
    )
    return EstimateResponse(
        food_id=food.id,
        food_name_fa=food.name_fa,
        portion_name_fa=portion.name_fa,
        quantity=request.quantity,
        estimated_grams=round(grams, 1),
        estimated_calories=round(calories, 1),
        calorie_range_min=round(range_min, 1),
        calorie_range_max=round(range_max, 1),
        confidence="medium",
    )
