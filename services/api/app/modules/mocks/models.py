from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Table,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.core.db import Base

attempts = Table(
    "mock_attempts",
    Base.metadata,
    Column("id", Uuid, primary_key=True),
    Column(
        "user_id",
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column("mock_exam_id", Text, ForeignKey("mock_exams.id"), nullable=False),
    Column("title", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("position", Integer, nullable=False),
    Column("started_at", DateTime(timezone=True), nullable=False),
    Column("deadline_at", DateTime(timezone=True)),
    Column("submitted_at", DateTime(timezone=True)),
    Column("result", JSONB(none_as_null=True)),
    CheckConstraint("mode IN ('timed','practice')", name="ck_mock_mode"),
    Index("ix_mock_expiry", "submitted_at", "deadline_at"),
)

slots = Table(
    "mock_answers",
    Base.metadata,
    Column(
        "attempt_id",
        Uuid,
        ForeignKey("mock_attempts.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("position", Integer, primary_key=True),
    Column("question_id", Text, ForeignKey("questions.id"), nullable=False),
    Column("snapshot", JSONB, nullable=False),
    Column("selected_option", Text),
    Column("flagged", Boolean, nullable=False, server_default="false"),
    Column("updated_at", DateTime(timezone=True)),
    CheckConstraint("selected_option IN ('A','B','C','D','E')", name="ck_mock_answer"),
    UniqueConstraint("attempt_id", "question_id", name="uq_mock_question"),
)
