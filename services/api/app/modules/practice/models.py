from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Table,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.core.db import Base

sessions = Table(
    "practice_sessions",
    Base.metadata,
    Column("id", Uuid, primary_key=True),
    Column(
        "user_id",
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column("kind", Text, nullable=False),
    Column("topic_id", Text, ForeignKey("topics.id"), nullable=False),
    Column("lesson_id", Text, ForeignKey("lessons.id")),
    Column("task_id", Uuid, ForeignKey("plan_tasks.id", ondelete="SET NULL"), index=True),
    Column("review_items", JSONB(none_as_null=True)),
    Column("question_ids", JSONB, nullable=False),
    Column("position", Integer, nullable=False),
    Column("state", Text, nullable=False),
    Column("started_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True)),
    CheckConstraint(
        "kind IN ('lesson_check','topic_test','review')", name="ck_practice_kind"
    ),
    CheckConstraint(
        "(kind = 'lesson_check') = (lesson_id IS NOT NULL)", name="ck_practice_lesson"
    ),
    CheckConstraint(
        "state IN ('question','feedback','ready','completed')", name="ck_practice_state"
    ),
    CheckConstraint(
        "position >= 1 AND position <= jsonb_array_length(question_ids)",
        name="ck_practice_position",
    ),
)
completions = Table(
    "lesson_completions",
    Base.metadata,
    Column("user_id", Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("lesson_id", Text, ForeignKey("lessons.id"), primary_key=True),
    Column("completed_at", DateTime(timezone=True), nullable=False),
)
mastery = Table(
    "mastery",
    Base.metadata,
    Column("user_id", Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("topic_id", Text, ForeignKey("topics.id"), primary_key=True),
    Column("value", Float, nullable=False),
    Column("answers_count", Integer, nullable=False),
    CheckConstraint(
        "value BETWEEN 0 AND 1 AND answers_count >= 0", name="ck_mastery_value"
    ),
)
reports = Table(
    "content_reports",
    Base.metadata,
    Column("id", Uuid, primary_key=True, server_default=func.gen_random_uuid()),
    Column("user_id", Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("question_id", Text, ForeignKey("questions.id"), index=True),
    Column("photo_solution_id", Uuid, ForeignKey("photo_solutions.id", ondelete="CASCADE")),
    Column("text", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("user_id", "question_id", name="uq_report_question"),
    UniqueConstraint("user_id", "photo_solution_id", name="uq_report_photo"),
    CheckConstraint(
        "num_nonnulls(question_id,photo_solution_id)=1", name="ck_report_target"
    ),
)
