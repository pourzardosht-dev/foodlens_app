# Recipe calculation workflow

Use [recipe-worksheet.csv](recipe-worksheet.csv) to record one standardized preparation of each selected food. Keep all weights in grams and use edible weights only.

## Required measurements

For every recipe:

1. Weigh each ingredient immediately before it is added.
2. Record oil actually added, including oil used for frying.
3. Do not count bones, pits, packaging, or discarded peels in edible weight.
4. After cooking, weigh the complete edible batch without the pot or serving dish.
5. Repeat `final_cooked_weight_g`, `food_id`, `food_name_fa`, and `uncertainty_percent` on every ingredient row for that recipe.
6. Add one row per ingredient. Copy the existing food row before adding more ingredients.

Water and salt may be omitted because they contribute none of the five V1 nutrients, but retained water is represented by the final cooked weight. Nutrient-bearing liquids, sauces, frying oil, garnishes, and toppings must be included.

## Ingredient nutrition source

Each ingredient row needs values per 100 g for kcal, protein, carbohydrate, fat, and fiber. Use one specific entry from a public or licensed database or a product label. Record a stable HTTPS URL or publication identifier in `source_reference` and the reuse terms in `licence_note`.

Do not use search-result snippets, unsourced blogs, generated values, or a range. For packaged milk or yogurt, record the exact product label and use the edible amount consumed. Keep a photo of the label outside Git for audit purposes.

## Calculation

For nutrient $n$, ingredient weights $w_i$, ingredient values per 100 g $v_{i,n}$, and final edible batch weight $W$:

$$
V_{recipe,n} = \frac{100}{W}\sum_i\frac{w_i v_{i,n}}{100}
$$

Generate the release after all 20 recipes have been reviewed:

```powershell
Set-Location D:\foodlens_app\backend
python scripts/calculate_recipe_release.py `
  ..\docs\recipe-worksheet.csv `
  ..\dataset\nutrition-release-2026-09.json `
  --release-id 2026-09-initial-20 `
  --reviewer-note "Recipes weighed and ingredient sources checked" `
  --effective-at 2026-09-05T00:00:00Z

python scripts/import_nutrition_release.py `
  ..\dataset\nutrition-release-2026-09.json
```

The first command calculates per-100-g values. The second validates the resulting release without writing to the database. Do not use `--apply` until the worksheet and generated release have been independently reviewed.