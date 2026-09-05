from decimal import Decimal

import pytest

from app.domain.nutrition import (
    Nutrients,
    WeightedNutrients,
    round_for_response,
    scale_nutrients,
    total_nutrients,
)


def test_scales_all_known_nutrients_with_decimal_arithmetic() -> None:
    result = scale_nutrients(
        Nutrients(
            kcal=Decimal("165"),
            protein_g=Decimal("8.2"),
            carb_g=Decimal("7.1"),
            fat_g=Decimal("11.5"),
            fiber_g=Decimal("2.4"),
        ),
        Decimal("180"),
    )

    assert result == Nutrients(
        kcal=Decimal("297"),
        protein_g=Decimal("14.76"),
        carb_g=Decimal("12.78"),
        fat_g=Decimal("20.70"),
        fiber_g=Decimal("4.32"),
    )


def test_missing_nutrient_makes_total_null_and_reports_weighted_completeness() -> None:
    result = total_nutrients(
        [
            WeightedNutrients(
                grams=Decimal("75"),
                nutrients=Nutrients(
                    kcal=Decimal("100"),
                    protein_g=Decimal("10"),
                    carb_g=None,
                    fat_g=Decimal("3"),
                    fiber_g=None,
                ),
            ),
            WeightedNutrients(
                grams=Decimal("25"),
                nutrients=Nutrients(
                    kcal=Decimal("50"),
                    protein_g=None,
                    carb_g=Decimal("5"),
                    fat_g=Decimal("2"),
                    fiber_g=None,
                ),
            ),
        ]
    )

    assert result.nutrients.kcal == Decimal("150")
    assert result.nutrients.protein_g is None
    assert result.completeness_percent["protein_g"] == 75
    assert result.completeness_percent["carb_g"] == 25
    assert result.completeness_percent["fiber_g"] == 0


def test_rejects_invalid_grams_and_rounds_only_at_boundary() -> None:
    nutrients = Nutrients(Decimal("1"), None, None, None, None)

    with pytest.raises(ValueError):
        scale_nutrients(nutrients, Decimal("0"))
    assert round_for_response(Decimal("12.349")) == Decimal("12.3")
    assert round_for_response(Decimal("12.350")) == Decimal("12.4")