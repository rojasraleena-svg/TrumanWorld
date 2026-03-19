"""rename director memory trigger_suspicion_score to trigger_subject_alert_score

Revision ID: 20260319_000002
Revises: 20260319_000001
Create Date: 2026-03-19

"""

from alembic import op


revision = "20260319_000002"
down_revision = "20260319_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("director_memories") as batch_op:
        batch_op.alter_column(
            "trigger_suspicion_score",
            new_column_name="trigger_subject_alert_score",
        )


def downgrade() -> None:
    with op.batch_alter_table("director_memories") as batch_op:
        batch_op.alter_column(
            "trigger_subject_alert_score",
            new_column_name="trigger_suspicion_score",
        )
