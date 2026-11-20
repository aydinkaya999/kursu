from sqlalchemy import (
    Column,
    Computed,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Table,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import ARRAY

from app.core.db import Base

quotes = Table(
    "price_assignments",
    Base.metadata,
    Column("user_id", Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("price_group", Integer, nullable=False),
    Column("amount", Integer, nullable=False),
)
counters = Table(
    "usage_counters",
    Base.metadata,
    Column("user_id", Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("counter", Text, primary_key=True),
    Column("period", Text, primary_key=True),
    Column("items", ARRAY(Text), nullable=False),
    Column("count", Integer, Computed("cardinality(items)", persisted=True)),
)
purchases = Table(
    "purchases",
    Base.metadata,
    Column("id", Uuid, primary_key=True),
    Column("user_id", Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("provider", Text, nullable=False),
    Column("provider_ref", Text, nullable=False),
    Column("amount", Integer, nullable=False),
    Column("currency", Text, nullable=False),
    Column("state", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("season", Date, nullable=False),
    UniqueConstraint("provider", "provider_ref", name="uq_purchase_receipt"),
    UniqueConstraint("user_id", "season", name="uq_purchase_season"),
)
