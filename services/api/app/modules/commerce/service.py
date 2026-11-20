import secrets
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.http import ISTANBUL, ApiError
from app.modules.accounts.models import users
from app.modules.commerce import access
from app.modules.commerce.models import counters, purchases, quotes
from app.modules.commerce.providers import (
    FakeNativeStore,
    NativePurchaseVerifier,
    WebCheckoutProvider,
)
from app.modules.commerce.schemas import Entitlement, NativePurchase, Paywall, Platform
from app.modules.notebook.models import entitlements


async def web_price(db: AsyncSession, user: UUID, prices: list[int]) -> int:
    amount = await db.scalar(select(quotes.c.amount).where(quotes.c.user_id == user))
    if amount is not None:
        return int(amount)
    # Serialize first quotes across users to balance even simultaneous assignments.
    await db.execute(select(func.pg_advisory_xact_lock(72201991)))
    counts = dict(
        (
            await db.execute(
                select(quotes.c.price_group, func.count()).group_by(quotes.c.price_group)
            )
        )
        .tuples()
        .all()
    )
    smallest = min(counts.get(i, 0) for i in range(len(prices)))
    group = secrets.choice([i for i in range(len(prices)) if counts.get(i, 0) == smallest])
    await db.execute(
        insert(quotes).values(user_id=user, price_group=group, amount=prices[group])
    )
    return prices[group]


async def offer(
    db: AsyncSession,
    user: UUID,
    now: datetime,
    platform: Platform,
    enabled: bool,
    secret: str,
) -> Paywall:
    cfg = await access.config(db)
    day = now.astimezone(ISTANBUL).date()
    available = enabled and day <= cfg.results_date
    return Paywall(
        results_date=cfg.results_date,
        limits=cfg.free_limits,
        platform=platform,
        amount_try=await web_price(db, user, cfg.web_price_groups_try)
        if platform == "web"
        else cfg.native_prices_try[platform],
        access=await access.entitlement(db, user, day),
        checkout_available=available,
        sandbox_receipt=FakeNativeStore(secret).receipt(user, cfg.exam_date, platform)
        if platform != "web" and available
        else None,
    )


async def purchase(
    db: AsyncSession,
    user: UUID,
    now: datetime,
    data: NativePurchase | None,
    web: WebCheckoutProvider | None,
    store: NativePurchaseVerifier | None,
) -> Entitlement:
    guest = await db.scalar(select(users.c.is_guest).where(users.c.id == user))
    if guest is not False:
        raise ApiError(403, "account_required", "Sign in before purchasing")
    cfg = await access.config(db)
    day = now.astimezone(ISTANBUL).date()
    if day > cfg.results_date:
        raise ApiError(409, "season_ended", "Season has ended")
    platform: Platform = data.platform if data else "web"
    existing = await access.entitlement(db, user, day)
    ref = None
    if data:
        if store is None:
            raise ApiError(503, "service_unavailable", "Store verifier unavailable")
        ref = store.verify(user, cfg.exam_date, data.platform, data.receipt)
    elif web is None:
        raise ApiError(503, "service_unavailable", "Checkout unavailable")
    if existing.active:
        return existing
    previous = (
        await db.execute(
            select(purchases.c.provider, purchases.c.provider_ref).where(
                purchases.c.user_id == user, purchases.c.season == cfg.exam_date
            )
        )
    ).one_or_none()
    if previous:
        platform, ref = previous.provider, previous.provider_ref
    else:
        if data:
            amount = cfg.native_prices_try[data.platform]
        else:
            assert web is not None
            amount = await web_price(db, user, cfg.web_price_groups_try)
            ref = web.checkout(user, cfg.exam_date, amount)
        await db.execute(
            insert(purchases).values(
                id=uuid4(),
                user_id=user,
                provider=platform,
                provider_ref=ref,
                amount=amount,
                currency="TRY",
                state="completed",
                season=cfg.exam_date,
                created_at=now,
            )
        )
    stmt = insert(entitlements).values(
        user_id=user,
        kind="season_pass",
        source=platform,
        valid_until=cfg.results_date,
        provider_ref=ref,
    )
    await db.execute(
        stmt.on_conflict_do_update(
            index_elements=["user_id", "kind"],
            set_={"valid_until": cfg.results_date, "source": platform, "provider_ref": ref},
        )
    )
    return await access.entitlement(db, user, day)


async def merge(db: AsyncSession, source: UUID, target: UUID) -> None:
    source_quote = (
        (await db.execute(select(quotes).where(quotes.c.user_id == source)))
        .mappings()
        .one_or_none()
    )
    if source_quote:
        await db.execute(
            insert(quotes)
            .values(**{**source_quote, "user_id": target})
            .on_conflict_do_nothing()
        )
    for row in (
        await db.execute(select(counters).where(counters.c.user_id == source))
    ).mappings():
        key = dict(user_id=target, counter=row["counter"], period=row["period"])
        prior = await db.scalar(select(counters.c["items"]).filter_by(**key))
        items = sorted(set(prior or []) | set(row["items"]))
        await db.execute(
            insert(counters)
            .values(**key, items=items)
            .on_conflict_do_update(
                index_elements=["user_id", "counter", "period"], set_={"items": items}
            )
        )
    # Purchases require a registered account. Also preserve historical guest receipts.
    known = select(purchases.c.season).where(purchases.c.user_id == target)
    await db.execute(
        update(purchases)
        .where(purchases.c.user_id == source, purchases.c.season.not_in(known))
        .values(user_id=target)
    )
