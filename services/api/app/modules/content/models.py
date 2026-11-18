"""PostgreSQL reference data and the offline content bank."""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Table,
    Text,
    UniqueConstraint,
    false,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.core.db import Base

metadata = Base.metadata
status_type = Enum(
    "draft",
    "prerelease",
    "published",
    "quarantined",
    "retired",
    native_enum=False,
    create_constraint=True,
    name="content_status",
)


def slug() -> Column[str]:
    return Column("id", Text, primary_key=True)


def placeholder() -> Column[bool]:
    return Column("is_placeholder", Boolean, nullable=False, server_default=false())


fields = Table(
    "fields",
    metadata,
    slug(),
    Column("name", Text, nullable=False),
    Column("score_type", Text, nullable=False),
    CheckConstraint("score_type IN ('P1', 'P2', 'P3')", name="ck_fields_score_type"),
)
subtests = Table(
    "subtests",
    metadata,
    slug(),
    Column("name", Text, nullable=False),
    Column("short_name", Text, nullable=False),
    Column("question_count", Integer, nullable=False),
    Column("exam_order", Integer, nullable=False),
    Column("weight_p1", Integer, nullable=False),
    UniqueConstraint("exam_order", deferrable=True, initially="DEFERRED"),
    CheckConstraint(
        "exam_order > 0 AND question_count > 0 AND weight_p1 BETWEEN 0 AND 100",
        name="ck_subtests_exam_facts",
    ),
)
remote_config = Table(
    "remote_config",
    metadata,
    Column("key", Text, primary_key=True),
    Column("value", JSONB, nullable=False),
)
topics = Table(
    "topics",
    metadata,
    slug(),
    Column("subtest_id", Text, ForeignKey("subtests.id"), nullable=False, index=True),
    Column("name", Text, nullable=False),
    Column("exam_weight", Float),
    placeholder(),
    UniqueConstraint("id", "subtest_id"),
    CheckConstraint("exam_weight >= 0", name="ck_topics_exam_weight"),
)
objectives = Table(
    "objectives",
    metadata,
    slug(),
    Column("topic_id", Text, ForeignKey("topics.id"), nullable=False),
    Column("text", Text, nullable=False),
    placeholder(),
    UniqueConstraint("id", "topic_id"),
)
misconceptions = Table(
    "misconceptions",
    metadata,
    slug(),
    Column("topic_id", Text, ForeignKey("topics.id"), nullable=False),
    Column("text", Text, nullable=False),
    placeholder(),
)
lessons = Table(
    "lessons",
    metadata,
    slug(),
    Column("topic_id", Text, ForeignKey("topics.id"), nullable=False, index=True),
    Column("title", Text, nullable=False),
    Column("minutes", Integer, nullable=False),
    Column("source", JSONB, nullable=False),
    Column("status", status_type, nullable=False),
    placeholder(),
    CheckConstraint("minutes BETWEEN 3 AND 5", name="ck_lessons_minutes"),
    Index("ix_lessons_source", "source", postgresql_using="gin"),
)
lesson_cards = Table(
    "lesson_cards",
    metadata,
    Column("lesson_id", Text, ForeignKey("lessons.id"), primary_key=True),
    Column("position", Integer, primary_key=True),
    Column("kind", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("blocks", JSONB, nullable=False),
    Column("tip", Text),
    CheckConstraint("position BETWEEN 1 AND 6", name="ck_lesson_cards_position"),
    CheckConstraint(
        "kind IN ('definition', 'example', 'confused', 'exam')", name="ck_lesson_cards_kind"
    ),
)
questions = Table(
    "questions",
    metadata,
    slug(),
    Column("subtest_id", Text, nullable=False),
    Column("topic_id", Text, nullable=False),
    Column("objective_id", Text, nullable=False, index=True),
    Column("difficulty", Integer, nullable=False),
    Column("stem", Text, nullable=False),
    Column("options", JSONB, nullable=False),
    Column("correct_option", Text, nullable=False),
    Column("rationales", JSONB, nullable=False),
    Column("solution_steps", JSONB, nullable=False),
    Column("source", JSONB, nullable=False),
    Column("related_lesson_id", Text, ForeignKey("lessons.id")),
    Column("status", status_type, nullable=False),
    placeholder(),
    ForeignKeyConstraint(
        ["topic_id", "subtest_id"],
        ["topics.id", "topics.subtest_id"],
        deferrable=True,
        initially="DEFERRED",
    ),
    ForeignKeyConstraint(
        ["objective_id", "topic_id"],
        ["objectives.id", "objectives.topic_id"],
        deferrable=True,
        initially="DEFERRED",
    ),
    CheckConstraint("difficulty BETWEEN 1 AND 3", name="ck_questions_difficulty"),
    CheckConstraint(
        "correct_option IN ('A', 'B', 'C', 'D', 'E')", name="ck_questions_correct_option"
    ),
    CheckConstraint(
        "NOT is_placeholder OR starts_with(stem, '[ÖRNEK]')",
        name="ck_questions_placeholder_stem",
    ),
    Index("ix_questions_subtest_difficulty", "subtest_id", "difficulty", "status"),
    Index("ix_questions_source", "source", postgresql_using="gin"),
)
lesson_check_questions = Table(
    "lesson_check_questions",
    metadata,
    Column("lesson_id", Text, primary_key=True),
    Column("position", Integer, primary_key=True),
    Column("question_id", Text, ForeignKey("questions.id"), nullable=False),
    Column("card_position", Integer, nullable=False),
    ForeignKeyConstraint(
        ["lesson_id", "card_position"],
        ["lesson_cards.lesson_id", "lesson_cards.position"],
        deferrable=True,
        initially="DEFERRED",
    ),
    UniqueConstraint("lesson_id", "question_id", deferrable=True, initially="DEFERRED"),
    CheckConstraint("position BETWEEN 1 AND 2", name="ck_lesson_checks_position"),
)
mock_exams = Table(
    "mock_exams",
    metadata,
    slug(),
    Column("title", Text, nullable=False),
    Column("status", status_type, nullable=False),
    Column("published_at", DateTime(timezone=True)),
    placeholder(),
)
mock_exam_questions = Table(
    "mock_exam_questions",
    metadata,
    Column("mock_exam_id", Text, ForeignKey("mock_exams.id"), primary_key=True),
    Column("position", Integer, primary_key=True),
    Column("question_id", Text, ForeignKey("questions.id"), nullable=False, index=True),
    UniqueConstraint("mock_exam_id", "question_id", deferrable=True, initially="DEFERRED"),
    CheckConstraint("position BETWEEN 1 AND 80", name="ck_mock_questions_position"),
)
