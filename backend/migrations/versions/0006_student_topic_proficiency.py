"""student_topic_proficiency

Revision ID: 0006_student_topic_proficiency
Revises: 0005_chunks_doc_id_idx
Create Date: 2026-09-16 20:10:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0006_student_topic_proficiency"
down_revision: str | None = "0005_chunks_doc_id_idx"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "student_topic_proficiency",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("topic_key", sa.String(length=80), nullable=False),
        sa.Column(
            "category",
            sa.String(length=40),
            nullable=False,
            server_default="morphosyntax",
        ),
        sa.Column(
            "mastery_score",
            sa.Float(),
            nullable=False,
            server_default="0.5",
        ),
        sa.Column(
            "attempts_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "correct_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "consecutive_successes",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "weakness_flags",
            JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "last_evaluated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "user_id", "topic_key", name="uq_user_topic_proficiency"
        ),
    )
    op.create_index(
        op.f("ix_student_topic_proficiency_user_id"),
        "student_topic_proficiency",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_student_topic_proficiency_topic_key"),
        "student_topic_proficiency",
        ["topic_key"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_student_topic_proficiency_topic_key"),
        table_name="student_topic_proficiency",
    )
    op.drop_index(
        op.f("ix_student_topic_proficiency_user_id"),
        table_name="student_topic_proficiency",
    )
    op.drop_table("student_topic_proficiency")
