from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Table,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.core.db import Base

plans = Table(
    "daily_plans",
    Base.metadata,
    Column("id", Uuid, primary_key=True),
    Column(
        "user_id",
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column("plan_date", Date, nullable=False),
    Column("needs_rebuild", Boolean, nullable=False, server_default="false"),
    Column("daily_minutes", Integer, nullable=False),
    Column("completed_at", DateTime(timezone=True)),
    UniqueConstraint("user_id", "plan_date"),
)
tasks = Table(
    "plan_tasks",
    Base.metadata,
    Column("id", Uuid, primary_key=True),
    Column(
        "plan_id",
        Uuid,
        ForeignKey("daily_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column("task_key", Text, nullable=False),
    Column("position", Integer, nullable=False),
    Column("type", Text, nullable=False),
    Column("ref", JSONB, nullable=False),
    Column("est_quarters", Integer, nullable=False),
    Column("state", Text, nullable=False),
    Column("included", Boolean, nullable=False),
    Column("completed_at", DateTime(timezone=True)),
    Column("carry_on", Date),
    Column("carried_on", Date),
    UniqueConstraint("plan_id", "task_key"),
    CheckConstraint("state IN ('pending','started','done')", name="ck_plan_task_state"),
    CheckConstraint(
        "type IN ('review','lesson','topic_test','mock')", name="ck_plan_task_type"
    ),
    CheckConstraint("est_quarters > 0", name="ck_plan_task_duration"),
)
streaks = Table(
    "streaks",
    Base.metadata,
    Column("user_id", Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("current", Integer, nullable=False),
    Column("longest", Integer, nullable=False),
    Column("last_completed_on", Date),
    Column("freeze_used_week", Date),
)
