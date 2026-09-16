"""roman_senate_badges

Revision ID: 0004_roman_senate_badges
Revises: 0003_alexandria_library_rag
Create Date: 2026-09-16 13:00:00.000000

"""

from collections.abc import Sequence
import uuid
from datetime import UTC, datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0004_roman_senate_badges"
down_revision: str | None = "0003_alexandria_library_rag"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

CANONIC_BADGES = [
    {
        "id": uuid.uuid4(),
        "code": "TIRO_PRIMUS",
        "title": "Tiro Primus",
        "latin_motto": "Initium sapientiae",
        "description": "Completou a primeira lição de latim clássico.",
        "icon_name": "Shield",
        "category": "completion",
        "tier": "bronze",
        "requirement_type": "lessons_count",
        "requirement_value": 1,
        "xp_reward": 50,
    },
    {
        "id": uuid.uuid4(),
        "code": "CENTURIO_STREAK_3",
        "title": "Centurio Fideli",
        "latin_motto": "Virtus in constantia",
        "description": "Manteve uma ofensiva de estudos de 3 dias consecutivos.",
        "icon_name": "Flame",
        "category": "streak",
        "tier": "silver",
        "requirement_type": "min_streak",
        "requirement_value": 3,
        "xp_reward": 100,
    },
    {
        "id": uuid.uuid4(),
        "code": "LEGATUS_STREAK_7",
        "title": "Legatus Legionis",
        "latin_motto": "Nulla dies sine linea",
        "description": "Alcançou uma semana inteira (7 dias) de ofensiva ininterrupta.",
        "icon_name": "Award",
        "category": "streak",
        "tier": "gold",
        "requirement_type": "min_streak",
        "requirement_value": 7,
        "xp_reward": 250,
    },
    {
        "id": uuid.uuid4(),
        "code": "CENSOR_SEVERUS",
        "title": "Censor Severus",
        "latin_motto": "Summa cum laude",
        "description": "Obteve nota 100 em avaliação rigorosa do Censor Latium.",
        "icon_name": "Scroll",
        "category": "score",
        "tier": "gold",
        "requirement_type": "perfect_score",
        "requirement_value": 100,
        "xp_reward": 150,
    },
    {
        "id": uuid.uuid4(),
        "code": "SENATOR_MODULE_1",
        "title": "Senator Romanus",
        "latin_motto": "Ad astra per aspera",
        "description": "Concluiu com êxito todas as lições do Módulo I: Fundamenta Linguae Latinae.",
        "icon_name": "Crown",
        "category": "completion",
        "tier": "laurel",
        "requirement_type": "module_complete",
        "requirement_value": 1,
        "xp_reward": 500,
    },
    {
        "id": uuid.uuid4(),
        "code": "SCRIBA_BIBLIOTHECA",
        "title": "Scriba Bibliothecae",
        "latin_motto": "Ex libris lux",
        "description": "Consultou fragmentos clássicos originais na Biblioteca de Alexandria.",
        "icon_name": "BookOpen",
        "category": "special",
        "tier": "bronze",
        "requirement_type": "library_search",
        "requirement_value": 1,
        "xp_reward": 50,
    },
    {
        "id": uuid.uuid4(),
        "code": "IMPERATOR_LATIUM",
        "title": "Imperator Latium",
        "latin_motto": "Veni, vidi, vici",
        "description": "Acumulou mais de 500 pontos totais de erudição clássica.",
        "icon_name": "Sparkles",
        "category": "score",
        "tier": "laurel",
        "requirement_type": "total_points",
        "requirement_value": 500,
        "xp_reward": 1000,
    },
]


def upgrade() -> None:
    # 1. Create badges table
    badges_table = op.create_table(
        "badges",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("latin_motto", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("icon_name", sa.String(length=64), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("tier", sa.String(length=32), server_default="bronze", nullable=False),
        sa.Column("requirement_type", sa.String(length=64), nullable=False),
        sa.Column("requirement_value", sa.Integer(), server_default="1", nullable=False),
        sa.Column("xp_reward", sa.Integer(), server_default="50", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_badges_code", "badges", ["code"], unique=True)
    op.create_index("ix_badges_category", "badges", ["category"])

    # 2. Create user_badges table
    op.create_table(
        "user_badges",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "badge_id",
            UUID(as_uuid=True),
            sa.ForeignKey("badges.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("unlocked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata", JSONB, server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),
    )
    op.create_index("ix_user_badges_user_id", "user_badges", ["user_id"])
    op.create_index("ix_user_badges_badge_id", "user_badges", ["badge_id"])

    # 3. Seed canonical Roman badges
    now = datetime.now(UTC)
    seed_data = [
        {
            **b,
            "created_at": now,
            "updated_at": now,
        }
        for b in CANONIC_BADGES
    ]
    op.bulk_insert(badges_table, seed_data)


def downgrade() -> None:
    op.drop_table("user_badges")
    op.drop_table("badges")
