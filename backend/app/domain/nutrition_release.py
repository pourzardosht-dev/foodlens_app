import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Food, FoodProfileVersion, NutritionSource


class NutritionSourceInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    source_type: Literal["government_db", "label", "recipe_calculation", "expert"]
    reference_url: str | None = None
    publication_id: str | None = Field(default=None, max_length=200)
    accessed_at: date
    licence_note: str = Field(min_length=1)

    @field_validator("reference_url")
    @classmethod
    def require_https(cls, value: str | None) -> str | None:
        if value is not None and not value.startswith("https://"):
            raise ValueError("reference_url must use HTTPS")
        return value

    @model_validator(mode="after")
    def require_reference(self) -> "NutritionSourceInput":
        if not self.reference_url and not self.publication_id:
            raise ValueError("source requires reference_url or publication_id")
        return self


class FoodNutritionInput(BaseModel):
    food_id: str = Field(min_length=1, max_length=100)
    kcal_per_100g: Decimal = Field(ge=0, le=10000)
    protein_g_per_100g: Decimal = Field(ge=0, le=1000)
    carb_g_per_100g: Decimal = Field(ge=0, le=1000)
    fat_g_per_100g: Decimal = Field(ge=0, le=1000)
    fiber_g_per_100g: Decimal = Field(ge=0, le=1000)
    uncertainty_percent: Decimal = Field(ge=0, le=100)


class NutritionRelease(BaseModel):
    release_id: str = Field(min_length=1, max_length=100)
    source: NutritionSourceInput
    review_state: Literal["source_checked", "nutritionist_reviewed"]
    reviewer_note: str = Field(min_length=1)
    effective_at: datetime
    foods: list[FoodNutritionInput]

    @model_validator(mode="after")
    def validate_release(self) -> "NutritionRelease":
        if self.effective_at.tzinfo is None or self.effective_at.utcoffset() is None:
            raise ValueError("effective_at must include a timezone offset")
        food_ids = [food.food_id for food in self.foods]
        if len(food_ids) != len(set(food_ids)):
            raise ValueError("food_id values must be unique")
        return self


def load_release(path: Path, *, expected_count: int = 20) -> NutritionRelease:
    release = NutritionRelease.model_validate_json(path.read_text(encoding="utf-8"))
    if len(release.foods) != expected_count:
        raise ValueError(
            f"release must contain exactly {expected_count} foods; got {len(release.foods)}"
        )
    return release


def apply_release(session: Session, release: NutritionRelease) -> int:
    food_ids = [item.food_id for item in release.foods]
    canonical_ids = set(
        session.scalars(
            select(Food.id).where(
                Food.id.in_(food_ids),
                Food.is_canonical.is_(True),
                Food.retired_at.is_(None),
            )
        ).all()
    )
    missing = sorted(set(food_ids) - canonical_ids)
    if missing:
        raise ValueError(f"unknown or non-canonical foods: {', '.join(missing)}")

    source = NutritionSource(**release.source.model_dump())
    session.add(source)
    session.flush()
    for item in release.foods:
        current_version = session.scalar(
            select(func.max(FoodProfileVersion.version)).where(
                FoodProfileVersion.food_id == item.food_id
            )
        )
        published = session.scalars(
            select(FoodProfileVersion).where(
                FoodProfileVersion.food_id == item.food_id,
                FoodProfileVersion.retired_at.is_(None),
                FoodProfileVersion.review_state.in_(
                    ("source_checked", "nutritionist_reviewed")
                ),
            )
        ).all()
        for version in published:
            version.retired_at = release.effective_at
        session.add(
            FoodProfileVersion(
                food_id=item.food_id,
                version=(current_version or 0) + 1,
                source_id=source.id,
                review_state=release.review_state,
                reviewer_note=release.reviewer_note,
                effective_at=release.effective_at,
                **item.model_dump(exclude={"food_id"}),
            )
        )
    session.flush()
    return len(release.foods)


def release_summary(release: NutritionRelease) -> str:
    return json.dumps(
        {
            "release_id": release.release_id,
            "review_state": release.review_state,
            "source": release.source.name,
            "food_count": len(release.foods),
            "food_ids": [item.food_id for item in release.foods],
        },
        ensure_ascii=False,
        indent=2,
    )