"""create personal nutrition schema

Revision ID: 758cfdb7d51f
Revises: 
Create Date: 2026-09-05 09:31:01.536304
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '758cfdb7d51f'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("timezone", sa.String(length=100), nullable=False),
        sa.Column("locale", sa.String(length=20), nullable=False),
        sa.Column("daily_calorie_target", sa.Numeric(8, 1), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_profiles"),
    )
    op.create_table(
        "nutrition_sources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("reference_url", sa.Text(), nullable=True),
        sa.Column("publication_id", sa.String(length=200), nullable=True),
        sa.Column("accessed_at", sa.Date(), nullable=False),
        sa.Column("licence_note", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_nutrition_sources"),
    )
    op.create_table(
        "profile_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["profile_id"], ["profiles.id"],
            name="fk_profile_tokens_profile_id_profiles", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_profile_tokens"),
        sa.UniqueConstraint("token_hash", name="uq_profile_tokens_token_hash"),
    )
    op.create_index(
        "ix_profile_tokens_profile_id", "profile_tokens", ["profile_id"]
    )
    op.create_table(
        "foods",
        sa.Column("id", sa.String(length=100), nullable=False),
        sa.Column("name_fa", sa.String(length=200), nullable=False),
        sa.Column("name_en", sa.String(length=200), nullable=False),
        sa.Column("family", sa.String(length=100), nullable=False),
        sa.Column("is_canonical", sa.Boolean(), nullable=False),
        sa.Column("owner_profile_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "(is_canonical AND owner_profile_id IS NULL) OR "
            "(NOT is_canonical AND owner_profile_id IS NOT NULL)",
            name="ck_foods_ownership_mode",
        ),
        sa.ForeignKeyConstraint(
            ["owner_profile_id"], ["profiles.id"],
            name="fk_foods_owner_profile_id_profiles", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_foods"),
    )
    op.create_index("ix_foods_owner_profile_id", "foods", ["owner_profile_id"])
    op.create_table(
        "food_aliases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("food_id", sa.String(length=100), nullable=False),
        sa.Column("locale", sa.String(length=20), nullable=False),
        sa.Column("alias", sa.String(length=200), nullable=False),
        sa.ForeignKeyConstraint(
            ["food_id"], ["foods.id"],
            name="fk_food_aliases_food_id_foods", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_food_aliases"),
        sa.UniqueConstraint("locale", "alias", name="uq_food_aliases_locale"),
    )
    op.create_index("ix_food_aliases_food_id", "food_aliases", ["food_id"])
    op.create_table(
        "food_profile_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("food_id", sa.String(length=100), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("review_state", sa.String(length=30), nullable=False),
        sa.Column("kcal_per_100g", sa.Numeric(10, 3), nullable=True),
        sa.Column("protein_g_per_100g", sa.Numeric(10, 3), nullable=True),
        sa.Column("carb_g_per_100g", sa.Numeric(10, 3), nullable=True),
        sa.Column("fat_g_per_100g", sa.Numeric(10, 3), nullable=True),
        sa.Column("fiber_g_per_100g", sa.Numeric(10, 3), nullable=True),
        sa.Column("uncertainty_percent", sa.Numeric(5, 2), nullable=False),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "review_state IN ('draft', 'source_checked', "
            "'nutritionist_reviewed', 'retired')",
            name="ck_food_profile_versions_review_state",
        ),
        sa.CheckConstraint(
            "uncertainty_percent >= 0 AND uncertainty_percent <= 100",
            name="ck_food_profile_versions_uncertainty_range",
        ),
        sa.CheckConstraint(
            "kcal_per_100g IS NULL OR kcal_per_100g >= 0",
            name="ck_food_profile_versions_kcal_nonnegative",
        ),
        sa.CheckConstraint(
            "protein_g_per_100g IS NULL OR protein_g_per_100g >= 0",
            name="ck_food_profile_versions_protein_nonnegative",
        ),
        sa.CheckConstraint(
            "carb_g_per_100g IS NULL OR carb_g_per_100g >= 0",
            name="ck_food_profile_versions_carb_nonnegative",
        ),
        sa.CheckConstraint(
            "fat_g_per_100g IS NULL OR fat_g_per_100g >= 0",
            name="ck_food_profile_versions_fat_nonnegative",
        ),
        sa.CheckConstraint(
            "fiber_g_per_100g IS NULL OR fiber_g_per_100g >= 0",
            name="ck_food_profile_versions_fiber_nonnegative",
        ),
        sa.ForeignKeyConstraint(
            ["food_id"], ["foods.id"],
            name="fk_food_profile_versions_food_id_foods", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["source_id"], ["nutrition_sources.id"],
            name="fk_food_profile_versions_source_id_nutrition_sources",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_food_profile_versions"),
        sa.UniqueConstraint(
            "food_id", "version", name="uq_food_profile_versions_food_id"
        ),
    )
    op.create_index(
        "ix_food_profile_versions_food_id", "food_profile_versions", ["food_id"]
    )
    op.create_index(
        "uq_food_profile_versions_active_published",
        "food_profile_versions",
        ["food_id"],
        unique=True,
        postgresql_where=sa.text(
            "retired_at IS NULL AND review_state IN "
            "('source_checked', 'nutritionist_reviewed')"
        ),
    )
    op.create_table(
        "food_portions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("food_id", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name_fa", sa.String(length=100), nullable=False),
        sa.Column("grams", sa.Numeric(10, 2), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=True),
        sa.CheckConstraint("grams > 0", name="ck_food_portions_grams_positive"),
        sa.ForeignKeyConstraint(
            ["food_id"], ["foods.id"],
            name="fk_food_portions_food_id_foods", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["source_id"], ["nutrition_sources.id"],
            name="fk_food_portions_source_id_nutrition_sources",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_food_portions"),
        sa.UniqueConstraint("food_id", "code", name="uq_food_portions_food_id"),
    )
    op.create_index("ix_food_portions_food_id", "food_portions", ["food_id"])
    op.create_index(
        "uq_food_portions_default",
        "food_portions",
        ["food_id"],
        unique=True,
        postgresql_where=sa.text("is_default"),
    )
    op.create_table(
        "meals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("meal_type", sa.String(length=20), nullable=False),
        sa.Column("eaten_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')",
            name="ck_meals_meal_type",
        ),
        sa.CheckConstraint(
            "source IN ('photo', 'manual', 'barcode', 'voice')",
            name="ck_meals_source",
        ),
        sa.CheckConstraint(
            "note IS NULL OR char_length(note) <= 500", name="ck_meals_note_length"
        ),
        sa.ForeignKeyConstraint(
            ["profile_id"], ["profiles.id"],
            name="fk_meals_profile_id_profiles", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_meals"),
    )
    op.create_index(
        "ix_meals_profile_eaten_at", "meals", ["profile_id", "eaten_at"]
    )
    op.create_table(
        "meal_components",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("meal_id", sa.Uuid(), nullable=False),
        sa.Column("food_id", sa.String(length=100), nullable=False),
        sa.Column("food_profile_version_id", sa.Uuid(), nullable=False),
        sa.Column("portion_code", sa.String(length=50), nullable=True),
        sa.Column("quantity", sa.Numeric(10, 3), nullable=True),
        sa.Column("grams", sa.Numeric(10, 2), nullable=False),
        sa.Column("recognition_confidence", sa.Numeric(5, 4), nullable=True),
        sa.Column("kcal_snapshot", sa.Numeric(12, 3), nullable=True),
        sa.Column("protein_g_snapshot", sa.Numeric(12, 3), nullable=True),
        sa.Column("carb_g_snapshot", sa.Numeric(12, 3), nullable=True),
        sa.Column("fat_g_snapshot", sa.Numeric(12, 3), nullable=True),
        sa.Column("fiber_g_snapshot", sa.Numeric(12, 3), nullable=True),
        sa.Column(
            "uncertainty_percent_snapshot", sa.Numeric(5, 2), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "grams > 0 AND grams <= 5000", name="ck_meal_components_grams_range"
        ),
        sa.CheckConstraint(
            "recognition_confidence IS NULL OR "
            "(recognition_confidence >= 0 AND recognition_confidence <= 1)",
            name="ck_meal_components_recognition_confidence_range",
        ),
        sa.CheckConstraint(
            "uncertainty_percent_snapshot >= 0 AND "
            "uncertainty_percent_snapshot <= 100",
            name="ck_meal_components_uncertainty_range",
        ),
        sa.ForeignKeyConstraint(
            ["food_id"], ["foods.id"],
            name="fk_meal_components_food_id_foods", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["food_profile_version_id"], ["food_profile_versions.id"],
            name="fk_meal_components_profile_version",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["meal_id"], ["meals.id"],
            name="fk_meal_components_meal_id_meals", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_meal_components"),
    )
    op.create_index(
        "ix_meal_components_meal_id", "meal_components", ["meal_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_meal_components_meal_id", table_name="meal_components")
    op.drop_table("meal_components")
    op.drop_index("ix_meals_profile_eaten_at", table_name="meals")
    op.drop_table("meals")
    op.drop_index("uq_food_portions_default", table_name="food_portions")
    op.drop_index("ix_food_portions_food_id", table_name="food_portions")
    op.drop_table("food_portions")
    op.drop_index(
        "uq_food_profile_versions_active_published",
        table_name="food_profile_versions",
    )
    op.drop_index(
        "ix_food_profile_versions_food_id", table_name="food_profile_versions"
    )
    op.drop_table("food_profile_versions")
    op.drop_index("ix_food_aliases_food_id", table_name="food_aliases")
    op.drop_table("food_aliases")
    op.drop_index("ix_foods_owner_profile_id", table_name="foods")
    op.drop_table("foods")
    op.drop_index("ix_profile_tokens_profile_id", table_name="profile_tokens")
    op.drop_table("profile_tokens")
    op.drop_table("nutrition_sources")
    op.drop_table("profiles")