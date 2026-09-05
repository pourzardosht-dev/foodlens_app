import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.auth import CurrentProfile, DatabaseSession
from app.db.models import Food, FoodPortion, FoodProfileVersion, NutritionSource


router = APIRouter(prefix="/v1/custom-foods", tags=["custom-foods"])


class CustomFoodCreate(BaseModel):
    name_fa: str = Field(min_length=1, max_length=200)
    name_en: str = Field(default="Custom food", min_length=1, max_length=200)
    kcal_per_100g: Decimal = Field(ge=0, le=10000)
    protein_g_per_100g: Decimal | None = Field(default=None, ge=0, le=1000)
    carb_g_per_100g: Decimal | None = Field(default=None, ge=0, le=1000)
    fat_g_per_100g: Decimal | None = Field(default=None, ge=0, le=1000)
    fiber_g_per_100g: Decimal | None = Field(default=None, ge=0, le=1000)
    uncertainty_percent: Decimal = Field(default=20, ge=0, le=100)
    portion_name_fa: str = Field(default="۱۰۰ گرم", min_length=1, max_length=100)
    portion_grams: Decimal = Field(default=100, gt=0, le=5000)


class CustomFoodUpdate(BaseModel):
    name_fa: str | None = Field(default=None, min_length=1, max_length=200)
    name_en: str | None = Field(default=None, min_length=1, max_length=200)
    kcal_per_100g: Decimal | None = Field(default=None, ge=0, le=10000)
    protein_g_per_100g: Decimal | None = Field(default=None, ge=0, le=1000)
    carb_g_per_100g: Decimal | None = Field(default=None, ge=0, le=1000)
    fat_g_per_100g: Decimal | None = Field(default=None, ge=0, le=1000)
    fiber_g_per_100g: Decimal | None = Field(default=None, ge=0, le=1000)
    uncertainty_percent: Decimal | None = Field(default=None, ge=0, le=100)
    portion_name_fa: str | None = Field(default=None, min_length=1, max_length=100)
    portion_grams: Decimal | None = Field(default=None, gt=0, le=5000)


class CustomFoodResponse(BaseModel):
    id: str
    name_fa: str
    name_en: str
    profile_version: int
    nutrition_status: str
    kcal_per_100g: float | None
    protein_g_per_100g: float | None
    carb_g_per_100g: float | None
    fat_g_per_100g: float | None
    fiber_g_per_100g: float | None
    uncertainty_percent: float
    portion_name_fa: str
    portion_grams: float


def _owned_food(session, profile_id: uuid.UUID, food_id: str) -> Food:
    food = session.scalar(
        select(Food).where(
            Food.id == food_id,
            Food.owner_profile_id == profile_id,
            Food.is_canonical.is_(False),
            Food.retired_at.is_(None),
        )
    )
    if food is None:
        raise HTTPException(status_code=404, detail="Custom food not found")
    return food


def _current_version(session, food_id: str) -> FoodProfileVersion:
    version = session.scalar(
        select(FoodProfileVersion)
        .where(
            FoodProfileVersion.food_id == food_id,
            FoodProfileVersion.retired_at.is_(None),
        )
        .order_by(FoodProfileVersion.version.desc())
        .limit(1)
    )
    if version is None:
        raise HTTPException(status_code=409, detail="Custom food has no active profile")
    return version


def _default_portion(session, food_id: str) -> FoodPortion:
    portion = session.scalar(
        select(FoodPortion).where(
            FoodPortion.food_id == food_id, FoodPortion.is_default.is_(True)
        )
    )
    if portion is None:
        raise HTTPException(status_code=409, detail="Custom food has no default portion")
    return portion


def _response(session, food: Food) -> CustomFoodResponse:
    version = _current_version(session, food.id)
    portion = _default_portion(session, food.id)
    return CustomFoodResponse(
        id=food.id,
        name_fa=food.name_fa,
        name_en=food.name_en,
        profile_version=version.version,
        nutrition_status="user_provided",
        kcal_per_100g=float(version.kcal_per_100g) if version.kcal_per_100g is not None else None,
        protein_g_per_100g=(
            float(version.protein_g_per_100g)
            if version.protein_g_per_100g is not None
            else None
        ),
        carb_g_per_100g=(
            float(version.carb_g_per_100g)
            if version.carb_g_per_100g is not None
            else None
        ),
        fat_g_per_100g=(
            float(version.fat_g_per_100g)
            if version.fat_g_per_100g is not None
            else None
        ),
        fiber_g_per_100g=(
            float(version.fiber_g_per_100g)
            if version.fiber_g_per_100g is not None
            else None
        ),
        uncertainty_percent=float(version.uncertainty_percent),
        portion_name_fa=portion.name_fa,
        portion_grams=float(portion.grams),
    )


@router.post("", response_model=CustomFoodResponse, status_code=status.HTTP_201_CREATED)
def create_custom_food(
    request: CustomFoodCreate,
    profile: CurrentProfile,
    session: DatabaseSession,
) -> CustomFoodResponse:
    now = datetime.now(UTC)
    food_id = f"custom-{uuid.uuid4()}"
    source = NutritionSource(
        name="User-provided nutrition data",
        source_type="user_provided",
        accessed_at=date.today(),
        licence_note="Private data entered by the profile owner.",
    )
    food = Food(
        id=food_id,
        name_fa=request.name_fa,
        name_en=request.name_en,
        family="custom",
        is_canonical=False,
        owner_profile_id=profile.id,
        created_at=now,
    )
    session.add_all([source, food])
    session.flush()
    session.add_all(
        [
            FoodProfileVersion(
                food_id=food.id,
                version=1,
                source_id=source.id,
                review_state="draft",
                kcal_per_100g=request.kcal_per_100g,
                protein_g_per_100g=request.protein_g_per_100g,
                carb_g_per_100g=request.carb_g_per_100g,
                fat_g_per_100g=request.fat_g_per_100g,
                fiber_g_per_100g=request.fiber_g_per_100g,
                uncertainty_percent=request.uncertainty_percent,
                effective_at=now,
            ),
            FoodPortion(
                food_id=food.id,
                code="default",
                name_fa=request.portion_name_fa,
                grams=request.portion_grams,
                is_default=True,
                source_id=source.id,
            ),
        ]
    )
    session.flush()
    return _response(session, food)


@router.get("", response_model=list[CustomFoodResponse])
def list_custom_foods(
    profile: CurrentProfile, session: DatabaseSession
) -> list[CustomFoodResponse]:
    foods = session.scalars(
        select(Food)
        .where(
            Food.owner_profile_id == profile.id,
            Food.is_canonical.is_(False),
            Food.retired_at.is_(None),
        )
        .order_by(Food.created_at)
    ).all()
    return [_response(session, food) for food in foods]


@router.patch("/{food_id}", response_model=CustomFoodResponse)
def update_custom_food(
    food_id: str,
    request: CustomFoodUpdate,
    profile: CurrentProfile,
    session: DatabaseSession,
) -> CustomFoodResponse:
    food = _owned_food(session, profile.id, food_id)
    current = _current_version(session, food.id)
    portion = _default_portion(session, food.id)
    changes = request.model_dump(exclude_unset=True)
    if "name_fa" in changes:
        food.name_fa = changes.pop("name_fa")
    if "name_en" in changes:
        food.name_en = changes.pop("name_en")
    if "portion_name_fa" in changes:
        portion.name_fa = changes.pop("portion_name_fa")
    if "portion_grams" in changes:
        portion.grams = changes.pop("portion_grams")
    now = datetime.now(UTC)
    current.retired_at = now
    source = NutritionSource(
        name="User-provided nutrition data",
        source_type="user_provided",
        accessed_at=date.today(),
        licence_note="Private data entered by the profile owner.",
    )
    session.add(source)
    session.flush()
    values = {
        field: changes.get(field, getattr(current, field))
        for field in (
            "kcal_per_100g",
            "protein_g_per_100g",
            "carb_g_per_100g",
            "fat_g_per_100g",
            "fiber_g_per_100g",
            "uncertainty_percent",
        )
    }
    session.add(
        FoodProfileVersion(
            food_id=food.id,
            version=current.version + 1,
            source_id=source.id,
            review_state="draft",
            effective_at=now,
            **values,
        )
    )
    session.flush()
    return _response(session, food)


@router.delete("/{food_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_custom_food(
    food_id: str,
    profile: CurrentProfile,
    session: DatabaseSession,
) -> Response:
    food = _owned_food(session, profile.id, food_id)
    now = datetime.now(UTC)
    food.retired_at = now
    _current_version(session, food.id).retired_at = now
    return Response(status_code=status.HTTP_204_NO_CONTENT)