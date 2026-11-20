from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    Table,
    Text,
    Uuid,
)

from app.core.db import Base

entries = Table(
    "mistake_entries",
    Base.metadata,
    Column("user_id", Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("entry_key", Text, primary_key=True),
    Column("objective_id", Text, ForeignKey("objectives.id"), nullable=False),
    Column("misconception_id", Text, ForeignKey("misconceptions.id")),
    Column("first_question_id", Text, ForeignKey("questions.id"), nullable=False),
    Column("last_answer_id", Uuid, nullable=False),
    Column("scheduled_on", Date, nullable=False),
    Column("due_on", Date),
    Column("interval_index", Integer, nullable=False),
    Column("correct_streak", Integer, nullable=False),
    Column("status", Text, nullable=False),
    CheckConstraint(
        "(status = 'open' AND due_on IS NOT NULL AND correct_streak BETWEEN 0 AND 2) "
        "OR (status = 'learned' AND due_on IS NULL AND correct_streak = 3)",
        name="ck_mistake_schedule",
    ),
    Index("ix_mistake_user_due", "user_id", "due_on"),
)

entitlements = Table(
    "entitlements",
    Base.metadata,
    Column("user_id", Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("kind", Text, primary_key=True),
    Column("valid_until", Date, nullable=False),
    Column("source", Text, nullable=False),
    Column("provider_ref", Text),
    CheckConstraint("kind = 'season_pass'", name="ck_entitlement_kind"),
    CheckConstraint("source IN ('web','ios','android')", name="ck_entitlement_source"),
)
