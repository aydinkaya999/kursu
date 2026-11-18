from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Table,
    Text,
    Time,
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
    Column("legacy_access", Boolean, nullable=False, server_default="true"),
)
profiles = Table(
    "profiles",
    Base.metadata,
    Column("user_id", Uuid, ForeignKey("users.id"), primary_key=True),
    Column("field_id", Text, ForeignKey("fields.id"), nullable=False),
    Column("score_type", Text, nullable=False),
    Column("daily_minutes", Integer, nullable=False),
    Column("attempt_kind", Text, nullable=False),
    Column("notification_time", Time),
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
    Column(
        "family_id", Uuid, nullable=False, index=True, server_default=func.gen_random_uuid()
    ),
    Column("expires_at", DateTime(timezone=True), nullable=False),
    Column("revoked_at", DateTime(timezone=True)),
)

identities = Table(
    "identities",
    Base.metadata,
    Column("provider", Text, primary_key=True),
    Column("subject", Text, primary_key=True),
    Column(
        "user_id",
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
)
email_codes = Table(
    "email_codes",
    Base.metadata,
    Column("email", Text, primary_key=True),
    Column("user_id", Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("code_hash", Text, nullable=False),
    Column("attempts", Integer, nullable=False),
    Column("sent_at", DateTime(timezone=True), nullable=False),
    Column("expires_at", DateTime(timezone=True), nullable=False),
)
provider_challenges = Table(
    "provider_challenges",
    Base.metadata,
    Column("state", Text, primary_key=True),
    Column("provider", Text, nullable=False),
    Column(
        "user_id",
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column("platform", Text, nullable=False),
    Column("nonce", Text, nullable=False),
    Column("pkce_verifier", Text, nullable=False),
    Column("subject", Text),
    Column("expires_at", DateTime(timezone=True), nullable=False),
)
