import uuid
from datetime import UTC, date as Date, datetime, time, timedelta
from decimal import Decimal
from typing import Annotated, Literal
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Query, Response, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from app.api.auth import CurrentProfile, DatabaseSession
from app.db.models import Food, FoodProfileVersion, Meal, MealComponent, Profile
from app.domain.nutrition import (
    Nutrients,
    WeightedNutrients,
    round_for_response,
    scale_nutrients,
    total_nutrients,
)


router = APIRouter(prefix="/v1", tags=["diary"])
MealType = Literal["breakfast", "lunch", "dinner", "snack"]
MealSource = Literal["photo", "manual"]


class ComponentInput(BaseModel):
    food_id: str = Field(min_length=1, max_length=100)
    grams: Decimal = Field(gt=0, le=5000)
    portion_code: str | None = Field(default=None, max_length=50)
    quantity: Decimal | None = Field(default=None, gt=0, le=100)
    recognition_confidence: Decimal | None = Field(default=None, ge=0, le=1)


class MealCreate(BaseModel):
    meal_type: MealType
    eaten_at: datetime
    source: MealSource
    note: str | None = Field(default=None, max_length=500)
    components: list[ComponentInput] = Field(min_length=1, max_length=8)

    @field_validator("eaten_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("eaten_at must include a timezone offset")
        return value


class MealUpdate(BaseModel):
    meal_type: MealType | None = None
    eaten_at: datetime | None = None
    note: str | None = Field(default=None, max_length=500)
    components: list[ComponentInput] | None = Field(default=None, min_length=1, max_length=8)

    @field_validator("eaten_at")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("eaten_at must include a timezone offset")
        return value


class NutrientResponse(BaseModel):
    kcal: float | None
    protein_g: float | None
    carb_g: float | None
    fat_g: float | None
    fiber_g: float | None


class ComponentResponse(BaseModel):
    id: str
    position: int
    food_id: str
    food_name_fa: str
    food_profile_version_id: str
    grams: float
    portion_code: str | None
    quantity: float | None
    recognition_confidence: float | None
    nutrients: NutrientResponse
    uncertainty_percent: float


class MealResponse(BaseModel):
    id: str
    meal_type: MealType
    eaten_at: datetime
    source: str
    note: str | None
    components: list[ComponentResponse]
    totals: NutrientResponse
    completeness_percent: dict[str, int]


class DiaryResponse(BaseModel):
    date: Date | None = None
    timezone: str
    totals: NutrientResponse
    completeness_percent: dict[str, int]
    meals: list[MealResponse]


def _float(value: Decimal | None) -> float | None:
    rounded = round_for_response(value)
    return float(rounded) if rounded is not None else None


def _nutrient_response(values: Nutrients) -> NutrientResponse:
    return NutrientResponse(
        kcal=_float(values.kcal),
        protein_g=_float(values.protein_g),
        carb_g=_float(values.carb_g),
        fat_g=_float(values.fat_g),
        fiber_g=_float(values.fiber_g),
    )


def _component_nutrients(component: MealComponent) -> Nutrients:
    return Nutrients(
        kcal=component.kcal_snapshot,
        protein_g=component.protein_g_snapshot,
        carb_g=component.carb_g_snapshot,
        fat_g=component.fat_g_snapshot,
        fiber_g=component.fiber_g_snapshot,
    )


def _meal_components(session: Session, meal_id: uuid.UUID) -> list[MealComponent]:
    return list(
        session.scalars(
            select(MealComponent)
            .where(MealComponent.meal_id == meal_id)
            .order_by(MealComponent.position)
        ).all()
    )


def _meal_response(session: Session, meal: Meal) -> MealResponse:
    components = _meal_components(session, meal.id)
    food_names = {
        food.id: food.name_fa
        for food in session.scalars(
            select(Food).where(Food.id.in_({item.food_id for item in components}))
        ).all()
    }
    weighted = [
        WeightedNutrients(component.grams, _component_nutrients(component))
        for component in components
    ]
    totals = total_nutrients(weighted)
    return MealResponse(
        id=str(meal.id),
        meal_type=meal.meal_type,
        eaten_at=meal.eaten_at,
        source=meal.source,
        note=meal.note,
        components=[
            ComponentResponse(
                id=str(component.id),
                position=component.position,
                food_id=component.food_id,
                food_name_fa=food_names[component.food_id],
                food_profile_version_id=str(component.food_profile_version_id),
                grams=float(component.grams),
                portion_code=component.portion_code,
                quantity=(float(component.quantity) if component.quantity else None),
                recognition_confidence=(
                    float(component.recognition_confidence)
                    if component.recognition_confidence is not None
                    else None
                ),
                nutrients=_nutrient_response(_component_nutrients(component)),
                uncertainty_percent=float(component.uncertainty_percent_snapshot),
            )
            for component in components
        ],
        totals=_nutrient_response(totals.nutrients),
        completeness_percent=totals.completeness_percent,
    )


def _owned_meal(session: Session, profile: Profile, meal_id: uuid.UUID) -> Meal:
    meal = session.scalar(
        select(Meal).where(Meal.id == meal_id, Meal.profile_id == profile.id)
    )
    if meal is None:
        raise HTTPException(status_code=404, detail="Meal not found")
    return meal


def _food_version(
    session: Session, profile: Profile, food_id: str
) -> FoodProfileVersion:
    version = session.scalar(
        select(FoodProfileVersion)
        .join(Food, Food.id == FoodProfileVersion.food_id)
        .where(
            Food.id == food_id,
            Food.retired_at.is_(None),
            or_(Food.is_canonical.is_(True), Food.owner_profile_id == profile.id),
            FoodProfileVersion.retired_at.is_(None),
        )
        .order_by(FoodProfileVersion.version.desc())
        .limit(1)
    )
    if version is None:
        raise HTTPException(status_code=422, detail=f"Food is unavailable: {food_id}")
    return version


def _new_component(
    session: Session,
    profile: Profile,
    meal_id: uuid.UUID,
    position: int,
    request: ComponentInput,
    now: datetime,
) -> MealComponent:
    version = _food_version(session, profile, request.food_id)
    nutrients = scale_nutrients(
        Nutrients(
            kcal=version.kcal_per_100g,
            protein_g=version.protein_g_per_100g,
            carb_g=version.carb_g_per_100g,
            fat_g=version.fat_g_per_100g,
            fiber_g=version.fiber_g_per_100g,
        ),
        request.grams,
    )
    return MealComponent(
        meal_id=meal_id,
        position=position,
        food_id=request.food_id,
        food_profile_version_id=version.id,
        portion_code=request.portion_code,
        quantity=request.quantity,
        grams=request.grams,
        recognition_confidence=request.recognition_confidence,
        kcal_snapshot=nutrients.kcal,
        protein_g_snapshot=nutrients.protein_g,
        carb_g_snapshot=nutrients.carb_g,
        fat_g_snapshot=nutrients.fat_g,
        fiber_g_snapshot=nutrients.fiber_g,
        uncertainty_percent_snapshot=version.uncertainty_percent,
        created_at=now,
        updated_at=now,
    )


def _replace_components(
    session: Session,
    profile: Profile,
    meal: Meal,
    requests: list[ComponentInput],
    now: datetime,
) -> None:
    session.execute(delete(MealComponent).where(MealComponent.meal_id == meal.id))
    session.add_all(
        [
            _new_component(session, profile, meal.id, position, request, now)
            for position, request in enumerate(requests)
        ]
    )
    session.flush()


@router.post("/meals", response_model=MealResponse, status_code=status.HTTP_201_CREATED)
def create_meal(
    request: MealCreate, profile: CurrentProfile, session: DatabaseSession
) -> MealResponse:
    now = datetime.now(UTC)
    meal = Meal(
        profile_id=profile.id,
        meal_type=request.meal_type,
        eaten_at=request.eaten_at.astimezone(UTC),
        source=request.source,
        note=request.note,
        created_at=now,
        updated_at=now,
    )
    session.add(meal)
    session.flush()
    _replace_components(session, profile, meal, request.components, now)
    return _meal_response(session, meal)


@router.get("/meals/{meal_id}", response_model=MealResponse)
def read_meal(
    meal_id: uuid.UUID, profile: CurrentProfile, session: DatabaseSession
) -> MealResponse:
    return _meal_response(session, _owned_meal(session, profile, meal_id))


@router.patch("/meals/{meal_id}", response_model=MealResponse)
def update_meal(
    meal_id: uuid.UUID,
    request: MealUpdate,
    profile: CurrentProfile,
    session: DatabaseSession,
) -> MealResponse:
    meal = _owned_meal(session, profile, meal_id)
    changes = request.model_dump(exclude_unset=True, exclude={"components"})
    if "eaten_at" in changes:
        changes["eaten_at"] = changes["eaten_at"].astimezone(UTC)
    for field, value in changes.items():
        setattr(meal, field, value)
    now = datetime.now(UTC)
    meal.updated_at = now
    if request.components is not None:
        _replace_components(session, profile, meal, request.components, now)
    session.flush()
    return _meal_response(session, meal)


@router.delete("/meals/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meal(
    meal_id: uuid.UUID, profile: CurrentProfile, session: DatabaseSession
) -> Response:
    meal = _owned_meal(session, profile, meal_id)
    session.delete(meal)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/meals/{meal_id}/components",
    response_model=MealResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_component(
    meal_id: uuid.UUID,
    request: ComponentInput,
    profile: CurrentProfile,
    session: DatabaseSession,
) -> MealResponse:
    meal = _owned_meal(session, profile, meal_id)
    components = _meal_components(session, meal.id)
    if len(components) >= 8:
        raise HTTPException(status_code=422, detail="A meal can have at most 8 components")
    now = datetime.now(UTC)
    session.add(_new_component(session, profile, meal.id, len(components), request, now))
    meal.updated_at = now
    session.flush()
    return _meal_response(session, meal)


@router.patch(
    "/meals/{meal_id}/components/{component_id}", response_model=MealResponse
)
def update_component(
    meal_id: uuid.UUID,
    component_id: uuid.UUID,
    request: ComponentInput,
    profile: CurrentProfile,
    session: DatabaseSession,
) -> MealResponse:
    meal = _owned_meal(session, profile, meal_id)
    component = session.scalar(
        select(MealComponent).where(
            MealComponent.id == component_id,
            MealComponent.meal_id == meal.id,
        )
    )
    if component is None:
        raise HTTPException(status_code=404, detail="Meal component not found")
    replacement = _new_component(
        session,
        profile,
        meal.id,
        component.position,
        request,
        datetime.now(UTC),
    )
    for field in (
        "food_id",
        "food_profile_version_id",
        "portion_code",
        "quantity",
        "grams",
        "recognition_confidence",
        "kcal_snapshot",
        "protein_g_snapshot",
        "carb_g_snapshot",
        "fat_g_snapshot",
        "fiber_g_snapshot",
        "uncertainty_percent_snapshot",
        "updated_at",
    ):
        setattr(component, field, getattr(replacement, field))
    meal.updated_at = component.updated_at
    session.flush()
    return _meal_response(session, meal)


@router.delete(
    "/meals/{meal_id}/components/{component_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_component(
    meal_id: uuid.UUID,
    component_id: uuid.UUID,
    profile: CurrentProfile,
    session: DatabaseSession,
) -> Response:
    meal = _owned_meal(session, profile, meal_id)
    component = session.scalar(
        select(MealComponent).where(
            MealComponent.id == component_id,
            MealComponent.meal_id == meal.id,
        )
    )
    if component is None:
        raise HTTPException(status_code=404, detail="Meal component not found")
    components = _meal_components(session, meal.id)
    if len(components) == 1:
        session.delete(meal)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    session.delete(component)
    session.flush()
    for position, remaining in enumerate(
        item for item in components if item.id != component.id
    ):
        remaining.position = position
    meal.updated_at = datetime.now(UTC)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _diary_response(
    session: Session,
    profile: Profile,
    meals: list[Meal],
    requested_date: Date | None,
) -> DiaryResponse:
    meal_responses = [_meal_response(session, meal) for meal in meals]
    weighted = [
        WeightedNutrients(component.grams, _component_nutrients(component))
        for meal in meals
        for component in _meal_components(session, meal.id)
    ]
    totals = total_nutrients(weighted)
    return DiaryResponse(
        date=requested_date,
        timezone=profile.timezone,
        totals=_nutrient_response(totals.nutrients),
        completeness_percent=totals.completeness_percent,
        meals=meal_responses,
    )


@router.get("/diary/day", response_model=DiaryResponse)
def read_diary_day(
    date_value: Annotated[Date, Query(alias="date")],
    profile: CurrentProfile,
    session: DatabaseSession,
) -> DiaryResponse:
    timezone = ZoneInfo(profile.timezone)
    start = datetime.combine(date_value, time.min, timezone).astimezone(UTC)
    end = start + timedelta(days=1)
    meals = list(
        session.scalars(
            select(Meal)
            .where(
                Meal.profile_id == profile.id,
                Meal.eaten_at >= start,
                Meal.eaten_at < end,
            )
            .order_by(Meal.eaten_at)
        ).all()
    )
    return _diary_response(session, profile, meals, date_value)


@router.get("/diary/range", response_model=list[MealResponse])
def read_diary_range(
    from_date: Annotated[Date, Query(alias="from")],
    to_date: Annotated[Date, Query(alias="to")],
    profile: CurrentProfile,
    session: DatabaseSession,
) -> list[MealResponse]:
    if to_date < from_date or (to_date - from_date).days > 31:
        raise HTTPException(status_code=422, detail="Date range must be 0 to 31 days")
    timezone = ZoneInfo(profile.timezone)
    start = datetime.combine(from_date, time.min, timezone).astimezone(UTC)
    end = datetime.combine(to_date + timedelta(days=1), time.min, timezone).astimezone(UTC)
    meals = session.scalars(
        select(Meal)
        .where(
            Meal.profile_id == profile.id,
            Meal.eaten_at >= start,
            Meal.eaten_at < end,
        )
        .order_by(Meal.eaten_at)
    ).all()
    return [_meal_response(session, meal) for meal in meals]