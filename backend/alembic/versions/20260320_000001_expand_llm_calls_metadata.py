"""expand llm_calls metadata for provider model and reasoning tokens

Revision ID: 20260320_000001
Revises: 89f84747caed
Create Date: 2026-03-20
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260320_000001"
down_revision: str | None = "89f84747caed"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("llm_calls", sa.Column("provider", sa.String(length=30), nullable=True))
    op.add_column("llm_calls", sa.Column("model", sa.String(length=100), nullable=True))
    op.add_column(
        "llm_calls",
        sa.Column("reasoning_tokens", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("llm_calls", "reasoning_tokens")
    op.drop_column("llm_calls", "model")
    op.drop_column("llm_calls", "provider")
