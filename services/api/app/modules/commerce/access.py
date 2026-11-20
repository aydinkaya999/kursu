from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.http import ISTANBUL, ApiError
from app.modules.commerce.models import counters
from app.modules.commerce.schemas import AccessConfig, Config, Entitlement
from app.modules.content.models import remote_config
from app.modules.notebook.models import entitlements
from app.modules.plan.models import plans


async def settings[T: BaseModel](db: AsyncSession, model: type[T]) -> T:
    rows = await db.execute(
        select(remote_config).where(remote_config.c.key.in_(model.model_fields))
    )
    try:
        return model.model_validate(dict(rows.tuples().all()))
    except ValueError as exc:
        raise ApiError(
            503, "service_unavailable", "Commerce configuration is incomplete"
        ) from exc


async def config(db: AsyncSession) -> Config:
    data = await settings(db, Config)
    if set(data.native_prices_try) != {"ios", "android"}:
        raise ApiError(503, "service_unavailable", "Storefront prices are missing")
    return data


async def entitlement(db: AsyncSession, user: UUID, day: date) -> Entitlement:
    row = (
        await db.execute(
            select(entitlements.c.valid_until, entitlements.c.source).where(
                entitlements.c.user_id == user, entitlements.c.kind == "season_pass"
            )
        )
    ).one_or_none()
    return Entitlement(
        active=bool(row and row.valid_until >= day),
        valid_until=row.valid_until if row else None,
        source=row.source if row else None,
    )


async def plan_access(db: AsyncSession, user: UUID, now: datetime) -> None:
    day = now.astimezone(ISTANBUL).date()
    if (await entitlement(db, user, day)).active:
        return
    first = await db.scalar(
        select(func.min(plans.c.plan_date)).where(plans.c.user_id == user)
    )
    if (day - (first or day)).days >= (
        await settings(db, AccessConfig)
    ).free_limits.plan_days:
        raise ApiError(
            403, "free_limit_reached", "Plan preview has ended", counter="plan_days"
        )


type Counter = Literal["mock_exams", "questions_per_day", "lessons_per_day"]


async def use(
    db: AsyncSession, user: UUID, now: datetime, counter: Counter, item: str
) -> None:
    """The caller locks the user. Re-reading a charged item is always idempotent."""
    day = now.astimezone(ISTANBUL).date()
    if (await entitlement(db, user, day)).active:
        return
    cfg = await settings(db, AccessConfig)
    period = (cfg.exam_date if counter == "mock_exams" else day).isoformat()
    keys = dict(user_id=user, counter=counter, period=period)
    existing = (await db.scalar(select(counters.c["items"]).filter_by(**keys))) or []
    if item in existing:
        return
    if len(existing) >= getattr(cfg.free_limits, counter):
        raise ApiError(403, "free_limit_reached", "Free allowance reached", counter=counter)
    items = [*existing, item]
    await db.execute(
        insert(counters)
        .values(**keys, items=items)
        .on_conflict_do_update(
            index_elements=["user_id", "counter", "period"], set_={"items": items}
        )
    )
