import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BadgeRead(BaseModel):
    """Canonical representation of a Roman Senate honor badge."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    title: str
    latin_motto: str
    description: str
    icon_name: str
    category: str
    tier: str
    requirement_type: str
    requirement_value: int
    xp_reward: int


class UserBadgeRead(BaseModel):
    """Badge unlocked by an authenticated student."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    badge_id: uuid.UUID
    badge: BadgeRead
    unlocked_at: datetime
    metadata_: dict[str, Any] = Field(
        default_factory=dict, serialization_alias="metadata"
    )


class SenateBadgeItem(BaseModel):
    """Combined model showing a badge with user's unlock status for the Senate Hall."""

    badge: BadgeRead
    is_unlocked: bool
    unlocked_at: datetime | None = None
    progress: int = Field(
        default=0,
        description="Progresso atual em direção ao requisito (ex: 2 de 3 dias)",
    )


class SenateBadgesOverviewResponse(BaseModel):
    """Full overview of all Senate badges with student's earned honors."""

    total_unlocked: int
    total_available: int
    completion_percentage: float
    badges: list[SenateBadgeItem]
