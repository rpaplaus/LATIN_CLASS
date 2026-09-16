import uuid
from typing import Any

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CourseModule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Represents a broader Latin learning module (e.g., First Declension, Basic Verbs)."""

    __tablename__ = "course_modules"

    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    level: Mapped[str] = mapped_column(String(50), default="beginner", nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    lessons: Mapped[list["Lesson"]] = relationship(
        "Lesson",
        back_populates="module",
        cascade="all, delete-orphan",
        order_by="Lesson.order_index",
    )

    def __repr__(self) -> str:
        return f"<CourseModule {self.title} (order={self.order_index})>"


class Lesson(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Represents an individual Latin lesson within a module."""

    __tablename__ = "lessons"

    module_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("course_modules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    pedagogical_objective: Mapped[str] = mapped_column(Text, nullable=False)
    grammar_topics: Mapped[list[Any]] = mapped_column(
        JSON, default=list, nullable=False
    )

    module: Mapped["CourseModule"] = relationship(
        "CourseModule", back_populates="lessons"
    )

    def __repr__(self) -> str:
        return f"<Lesson {self.title} (order={self.order_index})>"
