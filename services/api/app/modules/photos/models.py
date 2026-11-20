from sqlalchemy import Column, DateTime, ForeignKey, Table, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB

from app.core.db import Base

solutions = Table(
    "photo_solutions",
    Base.metadata,
    Column("id", Uuid, primary_key=True),
    Column("user_id", Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("request_id", Uuid, nullable=False),
    Column("result", JSONB, nullable=False),
    Column("expires_at", DateTime(timezone=True), nullable=False, index=True),
    UniqueConstraint("user_id", "request_id", name="uq_photo_request"),
)
