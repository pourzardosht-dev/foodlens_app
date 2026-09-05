"""seed development catalog v1

Revision ID: 1aaf982fa44b
Revises: 758cfdb7d51f
Create Date: 2026-09-05 13:42:16.421863
"""
import json
from collections.abc import Sequence
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from alembic import op
import sqlalchemy as sa


revision: str = '1aaf982fa44b'
down_revision: str | None = '758cfdb7d51f'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

nutrition_sources = sa.table(
    "nutrition_sources",
    sa.column("id", sa.Uuid()),
    sa.column("name", sa.String()),
    sa.column("source_type", sa.String()),
    sa.column("reference_url", sa.Text()),
    sa.column("publication_id", sa.String()),
    sa.column("accessed_at", sa.Date()),
    sa.column("licence_note", sa.Text()),
)
foods = sa.table(
    "foods",
    sa.column("id", sa.String()),
    sa.column("name_fa", sa.String()),
    sa.column("name_en", sa.String()),
    sa.column("family", sa.String()),
    sa.column("is_canonical", sa.Boolean()),
    sa.column("owner_profile_id", sa.Uuid()),
    sa.column("created_at", sa.DateTime(timezone=True)),
    sa.column("retired_at", sa.DateTime(timezone=True)),
)
food_profile_versions = sa.table(
    "food_profile_versions",
    sa.column("id", sa.Uuid()),
    sa.column("food_id", sa.String()),
    sa.column("version", sa.Integer()),
    sa.column("source_id", sa.Uuid()),
    sa.column("review_state", sa.String()),
    sa.column("kcal_per_100g", sa.Numeric()),
    sa.column("protein_g_per_100g", sa.Numeric()),
    sa.column("carb_g_per_100g", sa.Numeric()),
    sa.column("fat_g_per_100g", sa.Numeric()),
    sa.column("fiber_g_per_100g", sa.Numeric()),
    sa.column("uncertainty_percent", sa.Numeric()),
    sa.column("effective_at", sa.DateTime(timezone=True)),
    sa.column("retired_at", sa.DateTime(timezone=True)),
)
food_portions = sa.table(
    "food_portions",
    sa.column("id", sa.Uuid()),
    sa.column("food_id", sa.String()),
    sa.column("code", sa.String()),
    sa.column("name_fa", sa.String()),
    sa.column("grams", sa.Numeric()),
    sa.column("is_default", sa.Boolean()),
    sa.column("source_id", sa.Uuid()),
)


def _load_snapshot() -> dict[str, object]:
    path = Path(__file__).parents[1] / "data" / "catalog_v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def upgrade() -> None:
    snapshot = _load_snapshot()
    source = snapshot["source"]
    source["id"] = UUID(source["id"])
    source["accessed_at"] = date.fromisoformat(source["accessed_at"])
    op.bulk_insert(nutrition_sources, [source])

    food_rows = snapshot["foods"]
    for row in food_rows:
        row["created_at"] = datetime.fromisoformat(row["created_at"])
    op.bulk_insert(foods, food_rows)

    profile_rows = snapshot["profiles"]
    for row in profile_rows:
        row["id"] = UUID(row["id"])
        row["source_id"] = UUID(row["source_id"])
        row["kcal_per_100g"] = Decimal(row["kcal_per_100g"])
        row["uncertainty_percent"] = Decimal(row["uncertainty_percent"])
        row["effective_at"] = datetime.fromisoformat(row["effective_at"])
    op.bulk_insert(food_profile_versions, profile_rows)

    portion_rows = snapshot["portions"]
    for row in portion_rows:
        row["id"] = UUID(row["id"])
        row["source_id"] = UUID(row["source_id"])
        row["grams"] = Decimal(row["grams"])
    op.bulk_insert(food_portions, portion_rows)


def downgrade() -> None:
    snapshot = _load_snapshot()
    source_id = UUID(snapshot["source"]["id"])
    food_ids = [row["id"] for row in snapshot["foods"]]
    op.execute(food_portions.delete().where(food_portions.c.source_id == source_id))
    op.execute(
        food_profile_versions.delete().where(
            food_profile_versions.c.source_id == source_id
        )
    )
    op.execute(foods.delete().where(foods.c.id.in_(food_ids)))
    op.execute(nutrition_sources.delete().where(nutrition_sources.c.id == source_id))