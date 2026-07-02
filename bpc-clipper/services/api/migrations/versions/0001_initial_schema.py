"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-02
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False, server_default="unknown"),
        sa.Column("rights_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="created"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "sources",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("original_filename", sa.String(length=500), nullable=True),
        sa.Column("original_url", sa.Text(), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("storage_path", sa.Text(), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("fps", sa.Float(), nullable=True),
        sa.Column("video_codec", sa.String(length=80), nullable=True),
        sa.Column("audio_codec", sa.String(length=80), nullable=True),
        sa.Column("validation_status", sa.String(length=80), nullable=False, server_default="pending"),
        sa.Column("validation_message", sa.Text(), nullable=True),
        sa.Column("rights_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "jobs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("source_id", sa.String(), sa.ForeignKey("sources.id"), nullable=True),
        sa.Column("stage", sa.String(length=80), nullable=False, server_default="queued"),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="queued"),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "transcripts",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("source_id", sa.String(), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("language", sa.String(length=20), nullable=False, server_default="en"),
        sa.Column("provider", sa.String(length=80), nullable=False, server_default="mock"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "transcript_segments",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("transcript_id", sa.String(), sa.ForeignKey("transcripts.id"), nullable=False),
        sa.Column("speaker_label", sa.String(length=80), nullable=False, server_default="Speaker 1"),
        sa.Column("start_seconds", sa.Float(), nullable=False),
        sa.Column("end_seconds", sa.Float(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
    )

    op.create_table(
        "transcript_words",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("segment_id", sa.String(), sa.ForeignKey("transcript_segments.id"), nullable=False),
        sa.Column("start_seconds", sa.Float(), nullable=False),
        sa.Column("end_seconds", sa.Float(), nullable=False),
        sa.Column("text", sa.String(length=120), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("corrected_text", sa.String(length=120), nullable=True),
    )

    op.create_table(
        "candidate_clips",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("source_id", sa.String(), sa.ForeignKey("sources.id"), nullable=True),
        sa.Column("start_seconds", sa.Float(), nullable=False),
        sa.Column("end_seconds", sa.Float(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("risk_flags", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="candidate"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "edit_timelines",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("candidate_clip_id", sa.String(), sa.ForeignKey("candidate_clips.id"), nullable=False),
        sa.Column("start_seconds", sa.Float(), nullable=False),
        sa.Column("end_seconds", sa.Float(), nullable=False),
        sa.Column("hook_text", sa.Text(), nullable=True),
        sa.Column("caption_preset", sa.String(length=120), nullable=False, server_default="bpc_clean_editorial"),
        sa.Column("crop_mode", sa.String(length=80), nullable=False, server_default="speaker_focus"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
        sa.Column("settings", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "export_records",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("edit_timeline_id", sa.String(), sa.ForeignKey("edit_timelines.id"), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="queued"),
        sa.Column("format", sa.String(length=80), nullable=False, server_default="vertical_1080x1920"),
        sa.Column("include_burned_captions", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("include_srt", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("include_vtt", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("include_metadata", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("video_path", sa.Text(), nullable=True),
        sa.Column("srt_path", sa.Text(), nullable=True),
        sa.Column("vtt_path", sa.Text(), nullable=True),
        sa.Column("metadata_path", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("export_records")
    op.drop_table("edit_timelines")
    op.drop_table("candidate_clips")
    op.drop_table("transcript_words")
    op.drop_table("transcript_segments")
    op.drop_table("transcripts")
    op.drop_table("jobs")
    op.drop_table("sources")
    op.drop_table("projects")
