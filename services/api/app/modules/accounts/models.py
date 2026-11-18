from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Table,
    Text,
    Uuid,
    func,
)

from app.core.db import Base

users = Table(
    "users",
    Base.metadata,
    Column("id", Uuid, primary_key=True),
    Column("is_guest", Boolean, nullable=False),
    Column(
        "created_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
    Column("deleted_at", DateTime(timezone=True)),
)
profiles = Table(
    "profiles",
    Base.metadata,
    Column("user_id", Uuid, ForeignKey("users.id"), primary_key=True),
    Column("field_id", Text, ForeignKey("fields.id"), nullable=False),
    Column("score_type", Text, nullable=False),
    Column("daily_minutes", Integer, nullable=False),
    Column("attempt_kind", Text, nullable=False),
    CheckConstraint("score_type IN ('P1','P2','P3')", name="ck_profiles_score"),
    CheckConstraint("daily_minutes IN (30,60,90)", name="ck_profiles_minutes"),
    CheckConstraint("attempt_kind IN ('first','repeat')", name="ck_profiles_attempt"),
)
refresh_tokens = Table(
    "refresh_tokens",
    Base.metadata,
    Column("id", Uuid, primary_key=True),
    Column("user_id", Uuid, ForeignKey("users.id"), nullable=False, index=True),
    Column("token_hash", Text, unique=True, nullable=False),
    Column("expires_at", DateTime(timezone=True), nullable=False),
    Column("revoked_at", DateTime(timezone=True)),
)
