"""lesson_content_column

Revision ID: 0007_lesson_content
Revises: 0006_student_topic_proficiency
Create Date: 2026-09-17 19:15:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0007_lesson_content"
down_revision: str | None = "0006_student_topic_proficiency"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("lessons", sa.Column("content", JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("lessons", "content")
