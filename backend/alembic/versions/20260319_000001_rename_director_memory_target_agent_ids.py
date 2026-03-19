"""rename director memory target_cast_ids to target_agent_ids

Revision ID: 20260319_000001
Revises: 40f43097368d
Create Date: 2026-03-19

"""

from alembic import op


revision = "20260319_000001"
down_revision = "40f43097368d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("director_memories") as batch_op:
        batch_op.alter_column("target_cast_ids", new_column_name="target_agent_ids")


def downgrade() -> None:
    with op.batch_alter_table("director_memories") as batch_op:
        batch_op.alter_column("target_agent_ids", new_column_name="target_cast_ids")
