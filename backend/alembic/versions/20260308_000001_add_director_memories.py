"""add director_memories table

Revision ID: 20260308_000001
Revises: 20260307_000002
Create Date: 2026-03-08

"""

from alembic import op
import sqlalchemy as sa


revision = "20260308_000001"
down_revision = "20260307_000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "director_memories",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "run_id", sa.String(length=36), sa.ForeignKey("simulation_runs.id"), nullable=False
        ),
        sa.Column("tick_no", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("scene_goal", sa.String(length=50), nullable=False),
        sa.Column("target_cast_ids", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(length=20), nullable=False, server_default="advisory"),
        sa.Column("urgency", sa.String(length=20), nullable=False, server_default="advisory"),
        sa.Column("message_hint", sa.Text(), nullable=True),
        sa.Column("target_agent_id", sa.String(length=64), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("was_executed", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("effectiveness_score", sa.Float(), nullable=True),
        sa.Column("trigger_suspicion_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column(
            "trigger_continuity_risk", sa.String(length=20), nullable=False, server_default="stable"
        ),
        sa.Column("cooldown_ticks", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("cooldown_until_tick", sa.Integer(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_director_memories_run_id_tick_no", "director_memories", ["run_id", "tick_no"]
    )
    op.create_index(
        "ix_director_memories_run_id_scene_goal", "director_memories", ["run_id", "scene_goal"]
    )


def downgrade() -> None:
    op.drop_index("ix_director_memories_run_id_scene_goal", table_name="director_memories")
    op.drop_index("ix_director_memories_run_id_tick_no", table_name="director_memories")
    op.drop_table("director_memories")
