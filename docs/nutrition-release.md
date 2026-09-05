# Nutrition release workflow

Canonical nutrition values are published only from a reviewed JSON release. Do not infer or copy values without a source whose licence permits FoodLens use.

Each release must contain exactly 20 unique canonical food IDs by default, all five V1 nutrients per 100 g, uncertainty, a source reference, licence note, reviewer note, and a timezone-aware effective timestamp:

```json
{
  "release_id": "2026-09-initial-20",
  "source": {
    "name": "Licensed or public source name",
    "source_type": "government_db",
    "reference_url": "https://example.invalid/source",
    "publication_id": null,
    "accessed_at": "2026-09-05",
    "licence_note": "Record the actual reuse terms here."
  },
  "review_state": "source_checked",
  "reviewer_note": "Describe the review and recipe normalization method.",
  "effective_at": "2026-09-05T00:00:00Z",
  "foods": [
    {
      "food_id": "canonical-food-id",
      "kcal_per_100g": 0,
      "protein_g_per_100g": 0,
      "carb_g_per_100g": 0,
      "fat_g_per_100g": 0,
      "fiber_g_per_100g": 0,
      "uncertainty_percent": 0
    }
  ]
}
```

The numeric zeros above illustrate the schema only and are not nutrition data. Replace the example with reviewed values and 20 real catalog IDs.

Validate without database writes:

```powershell
Set-Location backend
python scripts/import_nutrition_release.py path/to/release.json
```

After review, apply it to a migrated database in one transaction:

```powershell
$env:DATABASE_URL="postgresql+psycopg://..."
python scripts/import_nutrition_release.py path/to/release.json --apply
```

The importer rejects incomplete nutrients, duplicate or unknown food IDs, invalid review states, missing source references, and releases that do not contain exactly 20 foods. Applying a release retires the previous published version while preserving diary snapshots.