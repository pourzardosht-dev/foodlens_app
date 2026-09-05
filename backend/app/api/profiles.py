import secrets
from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import delete, select

from app.api.auth import (
    CurrentProfile,
    DatabaseSession,
    hash_token,
    require_token_pepper,
)
from app.db.models import (
    Food,
    FoodPortion,
    FoodProfileVersion,
    Meal,
    MealComponent,
    NutritionSource,
    Profile,
    ProfileToken,
)
from app.observability import audit_event
from app.rate_limit import export_rate_limit, profile_creation_rate_limit
from app.settings import Settings, get_settings


router = APIRouter(prefix="/v1", tags=["profiles"])


class ProfileCreate(BaseModel):
    timezone: str = "Asia/Tehran"
    locale: str = Field(default="fa-IR", min_length=2, max_length=20)
    daily_calorie_target: Decimal | None = Field(default=None, gt=0, le=20000)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as error:
            raise ValueError("Timezone must be a valid IANA name") from error
        return value


class ProfileUpdate(BaseModel):
    timezone: str | None = None
    locale: str | None = Field(default=None, min_length=2, max_length=20)
    daily_calorie_target: Decimal | None = Field(default=None, gt=0, le=20000)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str | None) -> str | None:
        if value is None:
            return value
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as error:
            raise ValueError("Timezone must be a valid IANA name") from error
        return value


class ProfileResponse(BaseModel):
    id: str
    timezone: str
    locale: str
    daily_calorie_target: Decimal | None
    created_at: datetime
    updated_at: datetime


class AnonymousProfileResponse(ProfileResponse):
    token: str


def profile_response(profile: Profile) -> ProfileResponse:
    return ProfileResponse(
        id=str(profile.id),
        timezone=profile.timezone,
        locale=profile.locale,
        daily_calorie_target=profile.daily_calorie_target,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.post(
    "/profiles/anonymous",
    response_model=AnonymousProfileResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(profile_creation_rate_limit)],
)
def create_anonymous_profile(
    request: ProfileCreate,
    session: DatabaseSession,
    settings: Annotated[Settings, Depends(get_settings)],
) -> AnonymousProfileResponse:
    now = datetime.now(UTC)
    token = secrets.token_urlsafe(32)
    profile = Profile(
        timezone=request.timezone,
        locale=request.locale,
        daily_calorie_target=request.daily_calorie_target,
        created_at=now,
        updated_at=now,
    )
    session.add(profile)
    session.flush()
    session.add(
        ProfileToken(
            profile_id=profile.id,
            token_hash=hash_token(token, require_token_pepper(settings)),
            created_at=now,
            last_used_at=now,
        )
    )
    return AnonymousProfileResponse(**profile_response(profile).model_dump(), token=token)


@router.get("/profile", response_model=ProfileResponse)
def read_profile(profile: CurrentProfile) -> ProfileResponse:
    return profile_response(profile)


@router.patch("/profile", response_model=ProfileResponse)
def update_profile(
    request: ProfileUpdate,
    profile: CurrentProfile,
) -> ProfileResponse:
    changes = request.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(profile, field, value)
    profile.updated_at = datetime.now(UTC)
    return profile_response(profile)


@router.get("/profile/export", dependencies=[Depends(export_rate_limit)])
def export_profile(profile: CurrentProfile, session: DatabaseSession) -> dict[str, object]:
    meals = session.scalars(
        select(Meal).where(Meal.profile_id == profile.id).order_by(Meal.eaten_at)
    ).all()
    custom_foods = session.scalars(
        select(Food).where(Food.owner_profile_id == profile.id).order_by(Food.id)
    ).all()
    custom_food_ids = [food.id for food in custom_foods]
    custom_versions = session.scalars(
        select(FoodProfileVersion)
        .where(FoodProfileVersion.food_id.in_(custom_food_ids))
        .order_by(FoodProfileVersion.food_id, FoodProfileVersion.version)
    ).all()
    custom_portions = session.scalars(
        select(FoodPortion)
        .where(FoodPortion.food_id.in_(custom_food_ids))
        .order_by(FoodPortion.food_id, FoodPortion.code)
    ).all()
    versions_by_food: dict[str, list[dict[str, object]]] = {}
    for version in custom_versions:
        versions_by_food.setdefault(version.food_id, []).append(
            {
                "id": str(version.id),
                "version": version.version,
                "source_id": str(version.source_id),
                "review_state": version.review_state,
                "kcal_per_100g": version.kcal_per_100g,
                "protein_g_per_100g": version.protein_g_per_100g,
                "carb_g_per_100g": version.carb_g_per_100g,
                "fat_g_per_100g": version.fat_g_per_100g,
                "fiber_g_per_100g": version.fiber_g_per_100g,
                "uncertainty_percent": version.uncertainty_percent,
                "effective_at": version.effective_at.isoformat(),
                "retired_at": version.retired_at.isoformat()
                if version.retired_at is not None
                else None,
            }
        )
    portions_by_food: dict[str, list[dict[str, object]]] = {}
    for portion in custom_portions:
        portions_by_food.setdefault(portion.food_id, []).append(
            {
                "id": str(portion.id),
                "code": portion.code,
                "name_fa": portion.name_fa,
                "grams": portion.grams,
                "is_default": portion.is_default,
                "source_id": str(portion.source_id)
                if portion.source_id is not None
                else None,
            }
        )
    components = session.scalars(
        select(MealComponent)
        .join(Meal, Meal.id == MealComponent.meal_id)
        .where(Meal.profile_id == profile.id)
        .order_by(MealComponent.meal_id, MealComponent.position)
    ).all()
    components_by_meal: dict[str, list[dict[str, object]]] = {}
    for component in components:
        components_by_meal.setdefault(str(component.meal_id), []).append(
            {
                "id": str(component.id),
                "position": component.position,
                "food_id": component.food_id,
                "food_profile_version_id": str(component.food_profile_version_id),
                "portion_code": component.portion_code,
                "quantity": component.quantity,
                "grams": component.grams,
                "kcal_snapshot": component.kcal_snapshot,
                "protein_g_snapshot": component.protein_g_snapshot,
                "carb_g_snapshot": component.carb_g_snapshot,
                "fat_g_snapshot": component.fat_g_snapshot,
                "fiber_g_snapshot": component.fiber_g_snapshot,
                "uncertainty_percent_snapshot": (
                    component.uncertainty_percent_snapshot
                ),
            }
        )
    export = {
        "profile": profile_response(profile).model_dump(mode="json"),
        "meals": [
            {
                "id": str(meal.id),
                "meal_type": meal.meal_type,
                "eaten_at": meal.eaten_at.isoformat(),
                "source": meal.source,
                "note": meal.note,
                "components": components_by_meal.get(str(meal.id), []),
            }
            for meal in meals
        ],
        "custom_foods": [
            {
                "id": food.id,
                "name_fa": food.name_fa,
                "name_en": food.name_en,
                "retired_at": food.retired_at.isoformat()
                if food.retired_at is not None
                else None,
                "profile_versions": versions_by_food.get(food.id, []),
                "portions": portions_by_food.get(food.id, []),
            }
            for food in custom_foods
        ],
    }
    audit_event("profile_exported")
    return export


@router.delete("/profile", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(profile: CurrentProfile, session: DatabaseSession) -> Response:
    custom_food_ids = list(
        session.scalars(
            select(Food.id).where(Food.owner_profile_id == profile.id)
        ).all()
    )
    source_ids = set(
        session.scalars(
            select(FoodProfileVersion.source_id).where(
                FoodProfileVersion.food_id.in_(custom_food_ids)
            )
        ).all()
    )
    source_ids.update(
        session.scalars(
            select(FoodPortion.source_id).where(
                FoodPortion.food_id.in_(custom_food_ids),
                FoodPortion.source_id.is_not(None),
            )
        ).all()
    )
    session.execute(delete(Meal).where(Meal.profile_id == profile.id))
    if custom_food_ids:
        session.execute(
            delete(FoodPortion).where(FoodPortion.food_id.in_(custom_food_ids))
        )
        session.execute(
            delete(FoodProfileVersion).where(
                FoodProfileVersion.food_id.in_(custom_food_ids)
            )
        )
        session.execute(delete(Food).where(Food.id.in_(custom_food_ids)))
    if source_ids:
        session.execute(delete(NutritionSource).where(NutritionSource.id.in_(source_ids)))
    session.execute(delete(Profile).where(Profile.id == profile.id))
    audit_event("profile_deleted")
    return Response(status_code=status.HTTP_204_NO_CONTENT)