"""backfill missing memory columns safely

Revision ID: 20260312_000003
Revises: 20260312_000002
Create Date: 2026-03-12 10:30:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260312_000003"
down_revision: str | None = "20260312_000002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Some deployed databases were created before these fields were split into
    # forward migrations. Add every expected column defensively.
    op.execute(
        """
        ALTER TABLE memories
        ADD COLUMN IF NOT EXISTS event_importance DOUBLE PRECISION NOT NULL DEFAULT 0,
        ADD COLUMN IF NOT EXISTS self_relevance DOUBLE PRECISION NOT NULL DEFAULT 0,
        ADD COLUMN IF NOT EXISTS belief_confidence DOUBLE PRECISION NOT NULL DEFAULT 1,
        ADD COLUMN IF NOT EXISTS emotional_valence DOUBLE PRECISION NOT NULL DEFAULT 0,
        ADD COLUMN IF NOT EXISTS retrieval_count INTEGER NOT NULL DEFAULT 0,
        ADD COLUMN IF NOT EXISTS last_accessed_at TIMESTAMP WITH TIME ZONE NULL,
        ADD COLUMN IF NOT EXISTS streak_count INTEGER NOT NULL DEFAULT 1,
        ADD COLUMN IF NOT EXISTS last_tick_no INTEGER NULL
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE memories
        DROP COLUMN IF EXISTS last_tick_no,
        DROP COLUMN IF EXISTS streak_count,
        DROP COLUMN IF EXISTS last_accessed_at,
        DROP COLUMN IF EXISTS retrieval_count,
        DROP COLUMN IF EXISTS emotional_valence,
        DROP COLUMN IF EXISTS belief_confidence,
        DROP COLUMN IF EXISTS self_relevance,
        DROP COLUMN IF EXISTS event_importance
        """
    )
