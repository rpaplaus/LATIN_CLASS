"""user_vocabulary_favorites_table

Revision ID: 0008_user_vocabulary_favorites
Revises: 0007_lesson_content
Create Date: 2026-09-17 22:30:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0008_user_vocabulary_favorites"
down_revision: str | None = "0007_lesson_content"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_vocabulary_favorites",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("word", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "word", name="uq_user_vocabulary_favorite"),
    )
    op.create_index(
        "ix_user_vocabulary_favorites_user_id",
        "user_vocabulary_favorites",
        ["user_id"],
    )
    op.create_index(
        "ix_user_vocabulary_favorites_word",
        "user_vocabulary_favorites",
        ["word"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_user_vocabulary_favorites_word",
        table_name="user_vocabulary_favorites",
    )
    op.drop_index(
        "ix_user_vocabulary_favorites_user_id",
        table_name="user_vocabulary_favorites",
    )
    op.drop_table("user_vocabulary_favorites")
