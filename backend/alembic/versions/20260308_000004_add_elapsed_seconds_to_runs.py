"""add elapsed_seconds to simulation_runs

Revision ID: 20260308_000004
Revises: 20260308_000003
Create Date: 2026-03-08
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260308_000004"
down_revision: str | None = "20260308_000003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "simulation_runs",
        sa.Column("elapsed_seconds", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("simulation_runs", "elapsed_seconds")
