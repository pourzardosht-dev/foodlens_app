"""add food profile reviewer note

Revision ID: 6f3c2b8a91de
Revises: 3970e3579763
Create Date: 2026-09-05 18:00:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "6f3c2b8a91de"
down_revision: str | None = "3970e3579763"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "food_profile_versions",
        sa.Column("reviewer_note", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("food_profile_versions", "reviewer_note")
