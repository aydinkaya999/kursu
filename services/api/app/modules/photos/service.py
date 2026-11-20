import asyncio
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.http import ISTANBUL, ApiError
from app.modules.commerce import access
from app.modules.commerce.models import counters
from app.modules.commerce.schemas import PhotoLimits
from app.modules.content.models import lessons, topics
from app.modules.content.service import lesson_catalogue
from app.modules.photos.models import solutions
from app.modules.photos.schemas import (
    PhotoPolicy,
    PhotoQuota,
    PhotoResult,
    PhotoSolution,
    PhotoUpload,
    RelatedLesson,
)
from app.modules.photos.solver import Reading, VisionSolver
from app.modules.photos.storage import PhotoStore, normalize, preview
from app.modules.placement.service import lock_user


async def allowance(
    db: AsyncSession, user: UUID, now: datetime, limits: PhotoLimits
) -> tuple[PhotoQuota, str]:
    day = now.astimezone(ISTANBUL).date()
    paid = (await access.entitlement(db, user, day)).active
    period = day.isoformat() if paid else "lifetime"
    limit = limits.pass_daily if paid else limits.free_total
    used = await db.scalar(
        select(counters.c.count).filter_by(user_id=user, counter="photos", period=period)
    )
    return PhotoQuota(
        remaining=max(0, limit - (used or 0)), period="day" if paid else "lifetime"
    ), period


async def assess(db: AsyncSession, reading: Reading, threshold: float) -> PhotoResult:
    refused = PhotoResult(state="out_of_scope", is_placeholder=reading.is_placeholder)
    if not reading.in_scope:
        return refused
    topic = await db.scalar(select(topics.c.name).where(topics.c.id == reading.topic_id))
    if not topic:
        return refused
    lesson = (
        (
            await db.execute(
                lesson_catalogue()
                .where(lessons.c.topic_id == reading.topic_id)
                .order_by(lessons.c.is_placeholder, lessons.c.id)
                .limit(1)
            )
        )
        .mappings()
        .one_or_none()
    )
    result = PhotoResult(
        state="low_confidence",
        topic=topic,
        is_placeholder=reading.is_placeholder,
        lesson=RelatedLesson.model_validate(lesson) if lesson else None,
    )
    if (
        reading.confidence >= threshold
        and reading.question
        and reading.steps
        and reading.answer
    ):
        result.state = "solved"
        result.question = reading.question
        result.steps = reading.steps
        result.answer = reading.answer
    return result


async def read(
    db: AsyncSession, store: PhotoStore, user: UUID, id: UUID, now: datetime
) -> PhotoSolution:
    row = (
        await db.execute(
            select(solutions.c.result)
            .where(
                solutions.c.id == id,
                solutions.c.user_id == user,
                solutions.c.expires_at > now,
            )
            .with_for_update(read=True)
        )
    ).scalar_one_or_none()
    if row is None:
        raise ApiError(404, "not_found", "Photo unavailable")
    try:
        jpeg = await asyncio.to_thread(store.path(id).read_bytes)
        thumbnail = await asyncio.to_thread(preview, jpeg)
    except OSError as exc:
        raise ApiError(503, "service_unavailable", "Photo storage unavailable") from exc
    return PhotoSolution(
        id=id, result=PhotoResult.model_validate(row), preview_jpeg=thumbnail
    )


def file_lock(id: UUID) -> int:
    # Stable signed bigint for a transaction lock shared with orphan cleanup.
    return int.from_bytes(id.bytes[:8], signed=True)


async def create(
    db: AsyncSession,
    store: PhotoStore,
    solver: VisionSolver,
    user: UUID,
    data: PhotoUpload,
    now: datetime,
) -> PhotoSolution:
    await lock_user(db, user)
    existing = await db.scalar(
        select(solutions.c.id).filter_by(user_id=user, request_id=data.request_id)
    )
    if existing:
        return await read(db, store, user, existing, now)
    cfg = await access.settings(db, PhotoPolicy)
    quota, period = await allowance(db, user, now, cfg.photo_limits)
    if quota.remaining == 0:
        code = "free_limit_reached" if quota.period == "lifetime" else "daily_limit_reached"
        raise ApiError(403, code, "Photo allowance reached", counter="photos")
    jpeg = await asyncio.to_thread(normalize, data.image)
    reading = await solver.solve(jpeg)
    result = await assess(db, reading, cfg.photo_min_confidence)
    id = uuid4()
    thumbnail = await asyncio.to_thread(preview, jpeg)
    await db.execute(select(func.pg_advisory_xact_lock(file_lock(id))))
    await db.execute(
        solutions.insert().values(
            id=id,
            user_id=user,
            request_id=data.request_id,
            result=result.model_dump(),
            expires_at=now + timedelta(days=cfg.photo_retention_days),
        )
    )
    await access.record_use(db, user, "photos", period, str(id))
    try:
        await asyncio.to_thread(store.save, id, jpeg)
    except OSError as exc:
        raise ApiError(503, "service_unavailable", "Photo storage unavailable") from exc
    # A process interruption before commit leaves a private orphan for the deletion job.
    await db.commit()
    return PhotoSolution(id=id, result=result, preview_jpeg=thumbnail)


async def purge(db: AsyncSession, store: PhotoStore, now: datetime) -> int:
    # Delete expired metadata first. A failed or interrupted unlink remains retryable.
    await db.execute(delete(solutions).where(solutions.c.expires_at <= now))
    await db.commit()
    removed = 0
    files = await asyncio.to_thread(store.ids)
    for offset in range(0, len(files), 256):
        batch = files[offset : offset + 256]
        live = set(
            (
                await db.scalars(select(solutions.c.id).where(solutions.c.id.in_(batch)))
            ).all()
        )
        for id in set(batch) - live:
            locked = await db.scalar(select(func.pg_try_advisory_xact_lock(file_lock(id))))
            if locked and not await db.scalar(select(solutions.c.id).filter_by(id=id)):
                await asyncio.to_thread(store.remove, id)
                removed += 1
        await db.commit()
    return removed
