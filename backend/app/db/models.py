import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    MetaData,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)


class Base(DeclarativeBase):
    metadata = metadata


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    timezone: Mapped[str] = mapped_column(String(100), default="Asia/Tehran")
    locale: Mapped[str] = mapped_column(String(20), default="fa-IR")
    daily_calorie_target: Mapped[Decimal | None] = mapped_column(Numeric(8, 1))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ProfileToken(Base):
    __tablename__ = "profile_tokens"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[bytes] = mapped_column(LargeBinary, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Food(Base):
    __tablename__ = "foods"
    __table_args__ = (
        CheckConstraint(
            "(is_canonical AND owner_profile_id IS NULL) OR "
            "(NOT is_canonical AND owner_profile_id IS NOT NULL)",
            name="ownership_mode",
        ),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name_fa: Mapped[str] = mapped_column(String(200))
    name_en: Mapped[str] = mapped_column(String(200))
    family: Mapped[str] = mapped_column(String(100))
    is_canonical: Mapped[bool] = mapped_column(Boolean)
    owner_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    retired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class FoodAlias(Base):
    __tablename__ = "food_aliases"
    __table_args__ = (UniqueConstraint("locale", "alias"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    food_id: Mapped[str] = mapped_column(
        ForeignKey("foods.id", ondelete="CASCADE"), index=True
    )
    locale: Mapped[str] = mapped_column(String(20))
    alias: Mapped[str] = mapped_column(String(200))


class NutritionSource(Base):
    __tablename__ = "nutrition_sources"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    source_type: Mapped[str] = mapped_column(String(50))
    reference_url: Mapped[str | None] = mapped_column(Text)
    publication_id: Mapped[str | None] = mapped_column(String(200))
    accessed_at: Mapped[date] = mapped_column(Date)
    licence_note: Mapped[str] = mapped_column(Text)


class FoodProfileVersion(Base):
    __tablename__ = "food_profile_versions"
    __table_args__ = (
        UniqueConstraint("food_id", "version"),
        CheckConstraint(
            "review_state IN ('draft', 'source_checked', "
            "'nutritionist_reviewed', 'retired')",
            name="review_state",
        ),
        CheckConstraint(
            "uncertainty_percent >= 0 AND uncertainty_percent <= 100",
            name="uncertainty_range",
        ),
        CheckConstraint(
            "kcal_per_100g IS NULL OR kcal_per_100g >= 0",
            name="kcal_nonnegative",
        ),
        CheckConstraint(
            "protein_g_per_100g IS NULL OR protein_g_per_100g >= 0",
            name="protein_nonnegative",
        ),
        CheckConstraint(
            "carb_g_per_100g IS NULL OR carb_g_per_100g >= 0",
            name="carb_nonnegative",
        ),
        CheckConstraint(
            "fat_g_per_100g IS NULL OR fat_g_per_100g >= 0",
            name="fat_nonnegative",
        ),
        CheckConstraint(
            "fiber_g_per_100g IS NULL OR fiber_g_per_100g >= 0",
            name="fiber_nonnegative",
        ),
        Index(
            "uq_food_profile_versions_active_published",
            "food_id",
            unique=True,
            postgresql_where=text(
                "retired_at IS NULL AND review_state IN "
                "('source_checked', 'nutritionist_reviewed')"
            ),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    food_id: Mapped[str] = mapped_column(
        ForeignKey("foods.id", ondelete="RESTRICT"), index=True
    )
    version: Mapped[int] = mapped_column(Integer)
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("nutrition_sources.id", ondelete="RESTRICT")
    )
    review_state: Mapped[str] = mapped_column(String(30))
    kcal_per_100g: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    protein_g_per_100g: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    carb_g_per_100g: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    fat_g_per_100g: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    fiber_g_per_100g: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    uncertainty_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    effective_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    retired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class FoodPortion(Base):
    __tablename__ = "food_portions"
    __table_args__ = (
        UniqueConstraint("food_id", "code"),
        CheckConstraint("grams > 0", name="grams_positive"),
        Index(
            "uq_food_portions_default",
            "food_id",
            unique=True,
            postgresql_where=text("is_default"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    food_id: Mapped[str] = mapped_column(
        ForeignKey("foods.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(50))
    name_fa: Mapped[str] = mapped_column(String(100))
    grams: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    is_default: Mapped[bool] = mapped_column(Boolean)
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("nutrition_sources.id", ondelete="SET NULL")
    )


class Meal(Base):
    __tablename__ = "meals"
    __table_args__ = (
        CheckConstraint(
            "meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')",
            name="meal_type",
        ),
        CheckConstraint(
            "source IN ('photo', 'manual', 'barcode', 'voice')", name="source"
        ),
        CheckConstraint("note IS NULL OR char_length(note) <= 500", name="note_length"),
        Index("ix_meals_profile_eaten_at", "profile_id", "eaten_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE")
    )
    meal_type: Mapped[str] = mapped_column(String(20))
    eaten_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(String(20))
    note: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class MealComponent(Base):
    __tablename__ = "meal_components"
    __table_args__ = (
        CheckConstraint("grams > 0 AND grams <= 5000", name="grams_range"),
        CheckConstraint(
            "recognition_confidence IS NULL OR "
            "(recognition_confidence >= 0 AND recognition_confidence <= 1)",
            name="recognition_confidence_range",
        ),
        CheckConstraint(
            "uncertainty_percent_snapshot >= 0 AND "
            "uncertainty_percent_snapshot <= 100",
            name="uncertainty_range",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    meal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("meals.id", ondelete="CASCADE"), index=True
    )
    food_id: Mapped[str] = mapped_column(ForeignKey("foods.id", ondelete="RESTRICT"))
    food_profile_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "food_profile_versions.id",
            ondelete="RESTRICT",
            name="fk_meal_components_profile_version",
        )
    )
    portion_code: Mapped[str | None] = mapped_column(String(50))
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    grams: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    recognition_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    kcal_snapshot: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    protein_g_snapshot: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    carb_g_snapshot: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    fat_g_snapshot: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    fiber_g_snapshot: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    uncertainty_percent_snapshot: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))