"""modules_and_progress

Revision ID: 0002_modules_and_progress
Revises: 0001_initial_users
Create Date: 2026-09-16 11:00:00.000000

"""
import json
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON, UUID

revision: str = "0002_modules_and_progress"
down_revision: Union[str, None] = "0001_initial_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Course Modules Table
    course_modules_table = op.create_table(
        "course_modules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("level", sa.String(length=50), nullable=False, server_default="beginner"),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.text("true")),
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
    )

    # 2. Lessons Table
    lessons_table = op.create_table(
        "lessons",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "module_id",
            UUID(as_uuid=True),
            sa.ForeignKey("course_modules.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("pedagogical_objective", sa.Text(), nullable=False),
        sa.Column("grammar_topics", JSON(), nullable=False, server_default="[]"),
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
    )
    op.create_index(op.f("ix_lessons_module_id"), "lessons", ["module_id"], unique=False)

    # 3. User Progress Table
    op.create_table(
        "user_progress",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "current_module_id",
            UUID(as_uuid=True),
            sa.ForeignKey("course_modules.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "current_lesson_id",
            UUID(as_uuid=True),
            sa.ForeignKey("lessons.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("completed_lessons_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_streak_days", sa.Integer(), nullable=False, server_default="0"),
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
    )
    op.create_index(op.f("ix_user_progress_user_id"), "user_progress", ["user_id"], unique=True)

    # 4. Lesson Completions Table
    op.create_table(
        "lesson_completions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "lesson_id",
            UUID(as_uuid=True),
            sa.ForeignKey("lessons.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("score", sa.Integer(), nullable=False, server_default="100"),
        sa.Column(
            "completed_at",
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
        sa.UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson_completion"),
    )
    op.create_index(op.f("ix_lesson_completions_user_id"), "lesson_completions", ["user_id"], unique=False)
    op.create_index(op.f("ix_lesson_completions_lesson_id"), "lesson_completions", ["lesson_id"], unique=False)

    # 5. Insert Canonical Latin Seed Data
    mod1_id = uuid.uuid4()
    mod2_id = uuid.uuid4()

    op.bulk_insert(
        course_modules_table,
        [
            {
                "id": mod1_id,
                "order_index": 1,
                "title": "Módulo I: Fundamentos e a Primeira Declinação",
                "description": "Introdução à pronúncia clássica, geografia do Império Romano, desinências femininas em -a e o verbo de ligação esse.",
                "level": "beginner",
                "is_published": True,
            },
            {
                "id": mod2_id,
                "order_index": 2,
                "title": "Módulo II: A Segunda Declinação e Verbos Básicos",
                "description": "Substantivos masculinos (-us, -er) e neutros (-um), adjetivos de 1ª classe e presente do indicativo ativo.",
                "level": "beginner",
                "is_published": True,
            },
        ],
    )

    op.bulk_insert(
        lessons_table,
        [
            {
                "id": uuid.uuid4(),
                "module_id": mod1_id,
                "order_index": 1,
                "title": "Capítulo I: Imperium Romanum & Nominativo",
                "pedagogical_objective": "Aprender a estrutura da frase latina simples, o caso nominativo singular e plural da 1ª declinação e o verbo esse (est / sunt).",
                "grammar_topics": json.dumps(["1ª declinação (-a, -ae)", "caso nominativo", "est / sunt", "perguntas com -ne"]),
            },
            {
                "id": uuid.uuid4(),
                "module_id": mod1_id,
                "order_index": 2,
                "title": "Capítulo II: Familia Romana & Acusativo",
                "pedagogical_objective": "Compreender a função de objeto direto através do caso acusativo singular (-am) e relações de posse com o genitivo (-ae).",
                "grammar_topics": json.dumps(["caso acusativo (-am)", "caso genitivo (-ae)", "preposição in + ablativo", "vocabulário familiar"]),
            },
            {
                "id": uuid.uuid4(),
                "module_id": mod2_id,
                "order_index": 3,
                "title": "Capítulo III: Pueri et Viri & 2ª Declinação",
                "pedagogical_objective": "Dominar os substantivos masculinos da 2ª declinação e a concordância de adjetivos com substantivos de gêneros distintos.",
                "grammar_topics": json.dumps(["2ª declinação masculina (-us, -i)", "concordância nominal", "caso vocativo"]),
            },
            {
                "id": uuid.uuid4(),
                "module_id": mod2_id,
                "order_index": 4,
                "title": "Capítulo IV: Verba Latina & Presente do Indicativo",
                "pedagogical_objective": "Identificar as 4 conjugações verbais regulares latinas e conjugar verbos no presente do indicativo ativo.",
                "grammar_topics": json.dumps(["conjugações regulares (-are, -ere, -ere, -ire)", "desinências pessoais (-o, -s, -t, -mus, -tis, -nt)"]),
            },
        ],
    )


def downgrade() -> None:
    op.drop_table("lesson_completions")
    op.drop_table("user_progress")
    op.drop_table("lessons")
    op.drop_table("course_modules")
