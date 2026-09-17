import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.course import CourseModule, Lesson
from app.models.user import User


class UserProgress(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Tracks current learning state, streak and points for a Latin student."""

    __tablename__ = "user_progress"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    current_module_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("course_modules.id", ondelete="SET NULL"),
        nullable=True,
    )
    current_lesson_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lessons.id", ondelete="SET NULL"),
        nullable=True,
    )
    completed_lessons_count: Mapped[int] = mapped_column(Integer, default=0)
    total_points: Mapped[int] = mapped_column(Integer, default=0)
    current_streak_days: Mapped[int] = mapped_column(Integer, default=0)

    user: Mapped["User"] = relationship("User")
    current_module: Mapped["CourseModule | None"] = relationship("CourseModule")
    current_lesson: Mapped["Lesson | None"] = relationship("Lesson")

    def __repr__(self) -> str:
        return (
            f"<UserProgress user={self.user_id} "
            f"completed={self.completed_lessons_count} points={self.total_points}>"
        )


class LessonCompletion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Records completion score and timestamp for each completed lesson."""

    __tablename__ = "lesson_completions"
    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson_completion"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    score: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User")
    lesson: Mapped["Lesson"] = relationship("Lesson")

    def __repr__(self) -> str:
        return f"<LessonCompletion user={self.user_id} lesson={self.lesson_id} score={self.score}>"


class StudentTopicProficiency(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Tracks granular student proficiency across individual Latin grammar topics."""

    __tablename__ = "student_topic_proficiency"
    __table_args__ = (
        UniqueConstraint("user_id", "topic_key", name="uq_user_topic_proficiency"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    topic_key: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    category: Mapped[str] = mapped_column(
        String(40), nullable=False, default="morphosyntax"
    )
    mastery_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    attempts_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    correct_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    consecutive_successes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    weakness_flags: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    last_evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    user: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return (
            f"<StudentTopicProficiency user={self.user_id} "
            f"topic={self.topic_key} mastery={self.mastery_score:.2f}>"
        )


class UserVocabularyFavorite(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Stores Latin vocabulary terms favorited by a student in their personal notebook (Pugillares)."""

    __tablename__ = "user_vocabulary_favorites"
    __table_args__ = (
        UniqueConstraint("user_id", "word", name="uq_user_vocabulary_favorite"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    word: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    user: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return f"<UserVocabularyFavorite user={self.user_id} word='{self.word}'>"

