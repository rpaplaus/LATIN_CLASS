"""add_document_chunks_document_id_idx

Revision ID: 0005_chunks_doc_id_idx
Revises: 0004_roman_senate_badges
Create Date: 2026-09-16 14:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0005_chunks_doc_id_idx"
down_revision: str | None = "0004_roman_senate_badges"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        op.f("ix_document_chunks_document_id"),
        "document_chunks",
        ["document_id"],
        unique=False,
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_document_chunks_document_id"),
        table_name="document_chunks",
        if_exists=True,
    )
