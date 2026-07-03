"""add GameSense timeline events

Revision ID: 0003_gamesense_events
Revises: 0002_candidate_score_breakdown
Create Date: 2026-07-02
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_gamesense_events"
down_revision = "0002_candidate_score_breakdown"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "gamesense_events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("source_id", sa.String(), nullable=True),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("modality", sa.String(length=50), nullable=False),
        sa.Column("start_seconds", sa.Float(), nullable=False),
        sa.Column("end_seconds", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("intensity", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("evidence", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_gamesense_events_project_start", "gamesense_events", ["project_id", "start_seconds"])
    op.create_index("ix_gamesense_events_source_start", "gamesense_events", ["source_id", "start_seconds"])


def downgrade() -> None:
    op.drop_index("ix_gamesense_events_source_start", table_name="gamesense_events")
    op.drop_index("ix_gamesense_events_project_start", table_name="gamesense_events")
    op.drop_table("gamesense_events")
