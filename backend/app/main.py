import os

from fastapi import Depends, FastAPI, File, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError

from app.api.custom_foods import router as custom_foods_router
from app.api.meals import router as meals_router
from app.api.profiles import router as profiles_router
from app.db.models import Food, FoodPortion, FoodProfileVersion
from app.db.session import get_engine, session_scope
from app.nutrition import FOODS, estimate_calories, get_food
from app.observability import observe_request, render_metrics
from app.rate_limit import recognition_rate_limit
from app.settings import get_settings
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
    protein_g_per_100g: float | None = None
    carb_g_per_100g: float | None = None
    fat_g_per_100g: float | None = None
    fiber_g_per_100g: float | None = None
    nutrition_status: str = "draft"
    profile_version: int = 1
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
app.middleware("http")(observe_request)
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
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)
app.include_router(profiles_router)
app.include_router(meals_router)
app.include_router(custom_foods_router)


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(render_metrics(), media_type="text/plain; version=0.0.4")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/database")
def database_health() -> JSONResponse:
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
    except RuntimeError:
        return JSONResponse(status_code=503, content={"status": "not_configured"})
    except SQLAlchemyError:
        return JSONResponse(status_code=503, content={"status": "unavailable"})
    return JSONResponse(content={"status": "ok"})


@app.get("/v1/foods", response_model=list[FoodResponse])
def list_foods() -> list[FoodResponse]:
    if get_settings().app_env == "production":
        with session_scope() as session:
            return [
                _database_food_response(*item) for item in _published_foods(session)
            ]
    return [_fallback_food_response(food) for food in FOODS]


def _fallback_food_response(food) -> FoodResponse:
    return FoodResponse(
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


def _published_foods(
    session,
) -> list[tuple[Food, FoodProfileVersion, list[FoodPortion]]]:
    rows = session.execute(
        select(Food, FoodProfileVersion)
        .join(FoodProfileVersion, FoodProfileVersion.food_id == Food.id)
        .where(
            Food.is_canonical.is_(True),
            Food.retired_at.is_(None),
            FoodProfileVersion.retired_at.is_(None),
            FoodProfileVersion.review_state.in_(
                ("source_checked", "nutritionist_reviewed")
            ),
        )
        .order_by(Food.id, FoodProfileVersion.version.desc())
    ).all()
    current: dict[str, tuple[Food, FoodProfileVersion]] = {}
    for food, version in rows:
        current.setdefault(food.id, (food, version))
    if not current:
        return []
    portions = session.scalars(
        select(FoodPortion)
        .where(FoodPortion.food_id.in_(current))
        .order_by(FoodPortion.food_id, FoodPortion.code)
    ).all()
    portions_by_food: dict[str, list[FoodPortion]] = {}
    for portion in portions:
        portions_by_food.setdefault(portion.food_id, []).append(portion)
    return [
        (food, version, portions_by_food.get(food_id, []))
        for food_id, (food, version) in current.items()
    ]


def _database_food_response(
    food: Food, version: FoodProfileVersion, portions: list[FoodPortion]
) -> FoodResponse:
    default_portion = next((item for item in portions if item.is_default), None)
    if default_portion is None or version.kcal_per_100g is None:
        raise HTTPException(status_code=503, detail="Published catalog is invalid")
    return FoodResponse(
        id=food.id,
        name_fa=food.name_fa,
        name_en=food.name_en,
        kcal_per_100g=float(version.kcal_per_100g),
        uncertainty_percent=float(version.uncertainty_percent),
        protein_g_per_100g=float(version.protein_g_per_100g)
        if version.protein_g_per_100g is not None
        else None,
        carb_g_per_100g=float(version.carb_g_per_100g)
        if version.carb_g_per_100g is not None
        else None,
        fat_g_per_100g=float(version.fat_g_per_100g)
        if version.fat_g_per_100g is not None
        else None,
        fiber_g_per_100g=float(version.fiber_g_per_100g)
        if version.fiber_g_per_100g is not None
        else None,
        nutrition_status=version.review_state,
        profile_version=version.version,
        default_portion_id=default_portion.code,
        portions=[
            PortionResponse(
                id=portion.code,
                name_fa=portion.name_fa,
                grams=float(portion.grams),
            )
            for portion in portions
        ],
    )


@app.get("/v1/foods/{food_id}", response_model=FoodResponse)
def read_food(food_id: str) -> FoodResponse:
    if get_settings().app_env == "production":
        with session_scope() as session:
            match = next(
                (item for item in _published_foods(session) if item[0].id == food_id),
                None,
            )
            if match is None:
                raise HTTPException(status_code=404, detail="Food not found")
            return _database_food_response(*match)
    try:
        food = get_food(food_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Food not found") from error
    return _fallback_food_response(food)


@app.post(
    "/v1/recognition",
    response_model=RecognitionResult,
    dependencies=[Depends(recognition_rate_limit)],
)
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
