from collections import defaultdict
from collections.abc import Collection, Sequence
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import func, insert, select
from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.http import ISTANBUL, ApiError
from app.modules.content.models import questions
from app.modules.content.service import has_practice_feedback
from app.modules.notebook import service
from app.modules.notebook.models import entries
from app.modules.notebook.schemas import ReviewStart
from app.modules.placement.models import answers
from app.modules.placement.service import visible
from app.modules.practice.models import sessions


async def bank(
    db: AsyncSession, user: UUID, objectives: Collection[str]
) -> dict[str, list[str]]:
    result: dict[str, list[str]] = defaultdict(list)
    if not objectives:
        return result
    q, a = questions.c, answers.c
    history = (
        select(a.question_id, func.max(a.answered_at).label("seen"))
        .where(a.user_id == user)
        .group_by(a.question_id)
        .subquery()
    )
    rows = await db.execute(
        select(q.objective_id, q.id)
        .outerjoin(history, history.c.question_id == q.id)
        .where(
            q.objective_id.in_(objectives),
            q.status.in_(visible(user)),
            has_practice_feedback(),
        )
        .order_by(history.c.seen.asc().nulls_first(), q.is_placeholder, q.id)
    )
    for objective, question in rows:
        result[objective].append(question)
    return result


def sibling(
    candidates: Sequence[str], first: str, reserved: Collection[str] = ()
) -> str | None:
    return next((q for q in candidates if q != first and q not in reserved), None)


async def start(
    db: AsyncSession,
    user: UUID,
    data: ReviewStart,
    now: datetime,
    assigned: list[str] | None,
) -> UUID:
    day = now.astimezone(ISTANBUL).date()
    s = sessions.c
    scope = {"group_by": data.group_by, "group_id": data.group_id}
    resume = select(s.id).where(
        s.user_id == user,
        s.kind == "review",
        s.task_id == data.task_id,
        s.review_items["scope"] == scope,
    )
    active = await db.scalar(
        resume.where(s.state != "completed").order_by(s.started_at.desc(), s.id).limit(1)
    )
    if active:
        return UUID(str(active))
    items = await service.read(db, user, day, await service.calendar(db))
    eligible = [
        i
        for i in items
        if i.due is not None
        and (data.mode == "early" or i.due <= day)
        and (assigned is None or i.key in assigned)
        and (data.group_by is None or i.group(data.group_by)[0] == (data.group_id or ""))
    ]
    candidates = await bank(db, user, {i.objective for i in eligible})
    ids: list[str] = []
    slots = []
    topic = None
    for item in eligible:
        choice = sibling(candidates[item.objective], item.first_question, ids)
        if choice:
            ids.append(choice)
            slots.append({"key": item.key, "version": str(item.version)})
            topic = topic or item.topic
    if not ids:
        raise ApiError(
            409, "content_unavailable", "No eligible sibling questions for this review"
        )
    session = uuid4()
    await db.execute(
        insert(sessions).values(
            id=session,
            user_id=user,
            kind="review",
            topic_id=topic,
            task_id=data.task_id,
            review_items={"scope": scope, "slots": slots},
            question_ids=ids,
            position=1,
            state="question",
            started_at=now,
        )
    )
    return session


async def target(db: AsyncSession, row: RowMapping) -> RowMapping | None:
    slot = row["review_items"]["slots"][row["position"] - 1]
    return (
        (
            await db.execute(
                select(entries).where(
                    entries.c.user_id == row["user_id"],
                    entries.c.entry_key == slot["key"],
                    entries.c.status == "open",
                    entries.c.last_answer_id == UUID(slot["version"]),
                )
            )
        )
        .mappings()
        .one_or_none()
    )
