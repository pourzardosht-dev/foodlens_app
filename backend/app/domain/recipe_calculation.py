import csv
import hashlib
from collections import defaultdict
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

from app.domain.nutrition_release import (
    FoodNutritionInput,
    NutritionRelease,
    NutritionSourceInput,
)


NUTRIENT_FIELDS = (
    "kcal_per_100g",
    "protein_g_per_100g",
    "carb_g_per_100g",
    "fat_g_per_100g",
    "fiber_g_per_100g",
)


def calculate_recipe_release(
    path: Path,
    *,
    release_id: str,
    reviewer_note: str,
    effective_at: datetime,
    expected_count: int = 20,
) -> NutritionRelease:
    rows = list(csv.DictReader(path.read_text(encoding="utf-8-sig").splitlines()))
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if not row.get("food_id") or not row.get("ingredient_name"):
            continue
        grouped[row["food_id"].strip()].append(row)
    if len(grouped) != expected_count:
        raise ValueError(
            f"worksheet must contain exactly {expected_count} foods; got {len(grouped)}"
        )

    foods: list[FoodNutritionInput] = []
    source_references: set[str] = set()
    licence_notes: set[str] = set()
    for food_id, ingredients in grouped.items():
        final_weights = {
            Decimal(row["final_cooked_weight_g"]) for row in ingredients
        }
        if len(final_weights) != 1 or next(iter(final_weights)) <= 0:
            raise ValueError(f"{food_id}: final cooked weight must be one positive value")
        final_weight = next(iter(final_weights))
        uncertainty_values = {
            Decimal(row["uncertainty_percent"]) for row in ingredients
        }
        if len(uncertainty_values) != 1:
            raise ValueError(f"{food_id}: uncertainty must match on every row")
        totals = {field: Decimal("0") for field in NUTRIENT_FIELDS}
        for row in ingredients:
            ingredient_weight = Decimal(row["ingredient_edible_weight_g"])
            if ingredient_weight <= 0:
                raise ValueError(f"{food_id}: ingredient weights must be positive")
            for field in NUTRIENT_FIELDS:
                nutrient_value = Decimal(row[field])
                if nutrient_value < 0:
                    raise ValueError(f"{food_id}: ingredient nutrients cannot be negative")
                totals[field] += ingredient_weight * nutrient_value / Decimal("100")
            source_reference = row["source_reference"].strip()
            licence_note = row["licence_note"].strip()
            if not source_reference or not licence_note:
                raise ValueError(f"{food_id}: every ingredient needs source and licence")
            source_references.add(source_reference)
            licence_notes.add(licence_note)
        foods.append(
            FoodNutritionInput(
                food_id=food_id,
                uncertainty_percent=next(iter(uncertainty_values)),
                **{
                    field: (value / final_weight * Decimal("100")).quantize(
                        Decimal("0.001")
                    )
                    for field, value in totals.items()
                },
            )
        )

    reference_manifest = "; ".join(sorted(source_references))
    manifest_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    return NutritionRelease(
        release_id=release_id,
        source=NutritionSourceInput(
            name=f"Recipe calculation worksheet {release_id}",
            source_type="recipe_calculation",
            publication_id=f"recipe-worksheet-sha256:{manifest_hash}",
            accessed_at=date.today(),
            licence_note=" | ".join(sorted(licence_notes)),
        ),
        review_state="source_checked",
        reviewer_note=(
            f"{reviewer_note}\nIngredient source references: {reference_manifest}"
        ),
        effective_at=effective_at.astimezone(UTC),
        foods=foods,
    )