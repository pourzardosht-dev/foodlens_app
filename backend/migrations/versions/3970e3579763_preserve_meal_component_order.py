"""preserve meal component order

Revision ID: 3970e3579763
Revises: 1aaf982fa44b
Create Date: 2026-09-05 13:47:28.855022
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '3970e3579763'
down_revision: str | None = '1aaf982fa44b'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "meal_components",
        sa.Column("position", sa.Integer(), server_default="0", nullable=False),
    )
    op.create_check_constraint(
        "ck_meal_components_position_nonnegative",
        "meal_components",
        "position >= 0",
    )
    op.create_unique_constraint(
        "uq_meal_components_meal_id",
        "meal_components",
        ["meal_id", "position"],
    )
    op.alter_column("meal_components", "position", server_default=None)


def downgrade() -> None:
    op.drop_constraint(
        "uq_meal_components_meal_id", "meal_components", type_="unique"
    )
    op.drop_constraint(
        "ck_meal_components_position_nonnegative",
        "meal_components",
        type_="check",
    )
    op.drop_column("meal_components", "position")