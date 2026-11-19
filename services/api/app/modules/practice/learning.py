from collections import defaultdict
from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.content.models import lessons
from app.modules.placement.models import answers
from app.modules.practice.models import completions, mastery
from app.modules.practice.schemas import MasteryState


def outcome(correct: bool, unsure: bool) -> float:
    return (0.5 if unsure else 1.0) if correct else 0.0


def advance_mastery(value: float, score: float | None) -> float:
    return max(0.3, value) if score is None else value + 0.2 * (score - value)


def mastery_state(value: float, count: int, studied: bool) -> MasteryState:
    if not count and not studied:
        return "not_started"
    return "solid" if value >= 0.75 and count >= 8 else "in_progress"


def difficulty(value: float) -> int:
    return 1 if value < 0.4 else 2 if value < 0.75 else 3


async def refresh(db: AsyncSession, user: UUID, topic: str | None = None) -> None:
    """Replay canonical events so placement history, account merges and retries agree."""
    a = answers.c
    query = (
        select(a.topic_id, a.answered_at, a.is_correct, a.not_sure)
        .where(a.user_id == user, a.is_correct.is_not(None))
        .order_by(a.answered_at, a.placement_id, a.practice_id, a.position, a.id)
    )
    finished = (
        select(lessons.c.topic_id, completions.c.completed_at)
        .join_from(completions, lessons)
        .where(completions.c.user_id == user)
    )
    remove = delete(mastery).where(mastery.c.user_id == user)
    if topic is not None:
        query = query.where(a.topic_id == topic)
        finished = finished.where(lessons.c.topic_id == topic)
        remove = remove.where(mastery.c.topic_id == topic)
    events: list[tuple[datetime, str, float | None]] = [
        (r.answered_at, r.topic_id, outcome(r.is_correct, r.not_sure))
        for r in await db.execute(query)
    ]
    events.extend((r.completed_at, r.topic_id, None) for r in await db.execute(finished))
    values: dict[str, float] = defaultdict(float)
    counts: dict[str, int] = defaultdict(int)
    for _, key, score in sorted(events, key=lambda e: e[0]):
        values[key] = advance_mastery(values[key], score)
        counts[key] += int(score is not None)
    await db.execute(remove)
    if values:
        await db.execute(
            insert(mastery),
            [
                dict(user_id=user, topic_id=k, value=v, answers_count=counts[k])
                for k, v in values.items()
            ],
        )
