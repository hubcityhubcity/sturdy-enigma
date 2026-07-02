"""candidate score breakdown

Revision ID: 0002_candidate_score_breakdown
Revises: 0001_initial_schema
Create Date: 2026-07-02
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_candidate_score_breakdown"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("candidate_clips", sa.Column("score_breakdown", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("candidate_clips", "score_breakdown")
