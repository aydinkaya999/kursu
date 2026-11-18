from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.http import ApiError
from app.modules.accounts.models import (
    email_codes,
    identities,
    profiles,
    provider_challenges,
    refresh_tokens,
    users,
)
from app.modules.placement.models import answers, attempts


async def erase(db: AsyncSession, user: UUID) -> None:
    await db.execute(delete(answers).where(answers.c.user_id == user))
    await db.execute(delete(attempts).where(attempts.c.user_id == user))
    await db.execute(delete(profiles).where(profiles.c.user_id == user))
    await db.execute(delete(refresh_tokens).where(refresh_tokens.c.user_id == user))
    await db.execute(delete(users).where(users.c.id == user))


async def merge(db: AsyncSession, source: UUID, target: UUID) -> None:
    if not await db.scalar(select(profiles.c.user_id).where(profiles.c.user_id == target)):
        await db.execute(
            update(profiles).where(profiles.c.user_id == source).values(user_id=target)
        )
    if await db.scalar(
        select(attempts.c.id).where(
            attempts.c.user_id == target, attempts.c.state == "active"
        )
    ):
        await db.execute(
            update(attempts)
            .where(attempts.c.user_id == source, attempts.c.state == "active")
            .values(state="paused")
        )
    await db.execute(
        update(attempts).where(attempts.c.user_id == source).values(user_id=target)
    )
    collisions = select(answers.c.client_answer_id).where(answers.c.user_id == target)
    await db.execute(
        update(answers)
        .where(answers.c.user_id == source, answers.c.client_answer_id.in_(collisions))
        .values(client_answer_id=func.gen_random_uuid())
    )
    await db.execute(
        update(answers).where(answers.c.user_id == source).values(user_id=target)
    )
    await erase(db, source)


async def attach(db: AsyncSession, user: UUID, provider: str, subject: str) -> UUID:
    await db.execute(
        select(
            func.pg_advisory_xact_lock(func.hashtextextended(provider + ":" + subject, 0))
        )
    )
    target = await db.scalar(
        select(identities.c.user_id).where(
            identities.c.provider == provider, identities.c.subject == subject
        )
    )
    owners = dict(
        (
            await db.execute(
                select(users.c.id, users.c.is_guest)
                .where(users.c.id.in_({user, target or user}))
                .order_by(users.c.id)
                .with_for_update()
            )
        )
        .tuples()
        .all()
    )
    if user not in owners:
        raise ApiError(401, "unauthenticated", "Session changed")
    if not owners[user]:
        if target == user:
            return user
        raise ApiError(409, "conflict", "Sign out before changing accounts")
    if target is not None:
        await merge(db, user, target)
        return UUID(str(target))
    await db.execute(
        identities.insert().values(user_id=user, provider=provider, subject=subject)
    )
    await db.execute(
        update(users).where(users.c.id == user).values(is_guest=False, legacy_access=False)
    )
    await db.execute(delete(refresh_tokens).where(refresh_tokens.c.user_id == user))
    await db.execute(delete(email_codes).where(email_codes.c.user_id == user))
    await db.execute(
        delete(provider_challenges).where(provider_challenges.c.user_id == user)
    )
    return user
