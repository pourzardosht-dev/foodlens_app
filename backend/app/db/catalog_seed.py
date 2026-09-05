import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal

from app.nutrition import FOODS, RECOGNITION_FAMILIES


CATALOG_NAMESPACE = uuid.UUID("4c21d7f8-853a-4ed9-9d70-fc3f0b81e968")
SEED_SOURCE_ID = uuid.uuid5(CATALOG_NAMESPACE, "nutrition-source:development-seed-v1")
SEED_EFFECTIVE_AT = datetime(2026, 9, 5, tzinfo=UTC)
SEED_ACCESSED_AT = date(2026, 9, 5)


@dataclass(frozen=True)
class CatalogSeed:
    source: dict[str, object]
    foods: tuple[dict[str, object], ...]
    profiles: tuple[dict[str, object], ...]
    portions: tuple[dict[str, object], ...]


def build_catalog_seed() -> CatalogSeed:
    family_by_food = {
        food_id: family
        for family, food_ids in RECOGNITION_FAMILIES.items()
        for food_id in food_ids
    }
    foods: list[dict[str, object]] = []
    profiles: list[dict[str, object]] = []
    portions: list[dict[str, object]] = []

    for food in sorted(FOODS, key=lambda item: item.id):
        foods.append(
            {
                "id": food.id,
                "name_fa": food.name_fa,
                "name_en": food.name_en,
                "family": family_by_food[food.id],
                "is_canonical": True,
                "owner_profile_id": None,
                "created_at": SEED_EFFECTIVE_AT,
                "retired_at": None,
            }
        )
        profiles.append(
            {
                "id": uuid.uuid5(CATALOG_NAMESPACE, f"profile:{food.id}:1"),
                "food_id": food.id,
                "version": 1,
                "source_id": SEED_SOURCE_ID,
                "review_state": "draft",
                "kcal_per_100g": Decimal(str(food.kcal_per_100g)),
                "protein_g_per_100g": None,
                "carb_g_per_100g": None,
                "fat_g_per_100g": None,
                "fiber_g_per_100g": None,
                "uncertainty_percent": Decimal(str(food.uncertainty_percent)),
                "effective_at": SEED_EFFECTIVE_AT,
                "retired_at": None,
            }
        )
        for portion in sorted(food.portions, key=lambda item: item.id):
            portions.append(
                {
                    "id": uuid.uuid5(
                        CATALOG_NAMESPACE, f"portion:{food.id}:{portion.id}"
                    ),
                    "food_id": food.id,
                    "code": portion.id,
                    "name_fa": portion.name_fa,
                    "grams": Decimal(str(portion.grams)),
                    "is_default": portion.id == food.default_portion_id,
                    "source_id": SEED_SOURCE_ID,
                }
            )

    return CatalogSeed(
        source={
            "id": SEED_SOURCE_ID,
            "name": "FoodLens development seed catalog V1",
            "source_type": "internal_seed",
            "reference_url": None,
            "publication_id": "foodlens-seed-v1",
            "accessed_at": SEED_ACCESSED_AT,
            "licence_note": "Development estimates; not source-checked for publication.",
        },
        foods=tuple(foods),
        profiles=tuple(profiles),
        portions=tuple(portions),
    )