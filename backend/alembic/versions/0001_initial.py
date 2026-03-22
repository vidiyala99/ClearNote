"""initial

Revision ID: 0001_initial
Revises:
Create Date: 2026-03-14 00:00:00.000000

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUMs first
    visit_status = postgresql.ENUM(
        "pending", "processing", "ready", "failed",
        name="visit_status", create_type=False
    )
    visit_status.create(op.get_bind(), checkfirst=True)

    job_status = postgresql.ENUM(
        "queued", "processing", "done", "failed",
        name="job_status", create_type=False
    )
    job_status.create(op.get_bind(), checkfirst=True)

    urgency_tag = postgresql.ENUM(
        "normal", "follow-up", "referral", "prescription", "urgent",
        name="urgency_tag", create_type=False
    )
    urgency_tag.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("clerk_user_id", sa.String(100), nullable=False),
        sa.Column("preferred_language", sa.String(10), nullable=False, server_default="en"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("clerk_user_id"),
    )

    op.create_table(
        "visits",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("visit_date", sa.Date(), nullable=False),
        sa.Column("doctor_name", sa.String(200), nullable=True),
        sa.Column(
            "status",
            visit_status,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("audio_s3_key", sa.String(500), nullable=True),
        sa.Column("tags", sa.ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("consent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "jobs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("visit_id", sa.UUID(), nullable=False),
        sa.Column("s3_key", sa.String(500), nullable=False),
        sa.Column(
            "status",
            job_status,
            nullable=False,
            server_default="queued",
        ),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["visit_id"], ["visits.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("visit_id"),
    )

    op.create_table(
        "transcripts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("visit_id", sa.UUID(), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("chunks", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("language_detected", sa.String(10), nullable=False, server_default="en"),
        sa.Column("wer_confidence", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["visit_id"], ["visits.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("visit_id"),
    )

    op.create_table(
        "summaries",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("visit_id", sa.UUID(), nullable=False),
        sa.Column("overview", sa.Text(), nullable=True),
        sa.Column("medications", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("diagnoses", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("action_items", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column(
            "urgency_tag",
            urgency_tag,
            nullable=False,
            server_default="normal",
        ),
        sa.Column("translated_overview", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["visit_id"], ["visits.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("visit_id"),
    )


def downgrade() -> None:
    op.drop_table("summaries")
    op.drop_table("transcripts")
    op.drop_table("jobs")
    op.drop_table("visits")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS urgency_tag")
    op.execute("DROP TYPE IF EXISTS job_status")
    op.execute("DROP TYPE IF EXISTS visit_status")
