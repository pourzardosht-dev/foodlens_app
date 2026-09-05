from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


ONE_DECIMAL = Decimal("0.1")


@dataclass(frozen=True)
class Nutrients:
    kcal: Decimal | None
    protein_g: Decimal | None
    carb_g: Decimal | None
    fat_g: Decimal | None
    fiber_g: Decimal | None


@dataclass(frozen=True)
class WeightedNutrients:
    grams: Decimal
    nutrients: Nutrients


@dataclass(frozen=True)
class NutrientTotals:
    nutrients: Nutrients
    completeness_percent: dict[str, int]


def scale_nutrients(per_100g: Nutrients, grams: Decimal) -> Nutrients:
    if grams <= 0 or grams > Decimal("5000"):
        raise ValueError("grams must be greater than 0 and at most 5000")
    factor = grams / Decimal("100")
    return Nutrients(
        **{
            field: value * factor if value is not None else None
            for field, value in per_100g.__dict__.items()
        }
    )


def total_nutrients(components: list[WeightedNutrients]) -> NutrientTotals:
    total_grams = sum((item.grams for item in components), Decimal("0"))
    totals: dict[str, Decimal | None] = {}
    completeness: dict[str, int] = {}
    for field in Nutrients.__dataclass_fields__:
        known = [item for item in components if getattr(item.nutrients, field) is not None]
        known_grams = sum((item.grams for item in known), Decimal("0"))
        completeness[field] = (
            int((known_grams * 100 / total_grams).quantize(Decimal("1")))
            if total_grams
            else 100
        )
        totals[field] = (
            sum((getattr(item.nutrients, field) for item in known), Decimal("0"))
            if len(known) == len(components)
            else None
        )
    return NutrientTotals(Nutrients(**totals), completeness)


def round_for_response(value: Decimal | None) -> Decimal | None:
    return value.quantize(ONE_DECIMAL, rounding=ROUND_HALF_UP) if value is not None else None