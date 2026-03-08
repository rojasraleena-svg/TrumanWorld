"""add started_at to simulation_runs

Revision ID: 20260308_000003
Revises: 20260308_000002
Create Date: 2026-03-08
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260308_000003"
down_revision: str | None = "20260308_000002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "simulation_runs",
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("simulation_runs", "started_at")
