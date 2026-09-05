from datetime import UTC, datetime

import pytest

from app.domain.recipe_calculation import calculate_recipe_release


HEADER = (
    "food_id,food_name_fa,final_cooked_weight_g,ingredient_name,"
    "ingredient_edible_weight_g,kcal_per_100g,protein_g_per_100g,"
    "carb_g_per_100g,fat_g_per_100g,fiber_g_per_100g,"
    "uncertainty_percent,source_reference,licence_note\n"
)


def test_recipe_uses_final_cooked_weight_and_sums_ingredients(tmp_path) -> None:
    worksheet = tmp_path / "recipes.csv"
    worksheet.write_text(
        HEADER
        + "test-food,test,200,ingredient-a,100,100,10,20,5,2,15,source-a,public\n"
        + "test-food,test,200,ingredient-b,50,200,20,10,10,4,15,source-b,public\n",
        encoding="utf-8",
    )

    release = calculate_recipe_release(
        worksheet,
        release_id="test",
        reviewer_note="Reviewed fixture",
        effective_at=datetime(2026, 9, 5, tzinfo=UTC),
        expected_count=1,
    )
    food = release.foods[0]

    assert food.kcal_per_100g == 100
    assert food.protein_g_per_100g == 10
    assert food.carb_g_per_100g == 12.5
    assert food.fat_g_per_100g == 5
    assert food.fiber_g_per_100g == 2
    assert release.source.publication_id.startswith("recipe-worksheet-sha256:")
    assert "source-a; source-b" in release.reviewer_note


def test_recipe_rejects_missing_source(tmp_path) -> None:
    worksheet = tmp_path / "recipes.csv"
    worksheet.write_text(
        HEADER + "test-food,test,100,ingredient,100,100,1,2,3,4,10,,\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="source and licence"):
        calculate_recipe_release(
            worksheet,
            release_id="test",
            reviewer_note="Reviewed fixture",
            effective_at=datetime(2026, 9, 5, tzinfo=UTC),
            expected_count=1,
        )