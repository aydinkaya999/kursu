from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import date
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.http import ISTANBUL, ApiError
from app.modules.content import models as content
from app.modules.notebook.models import entitlements, entries
from app.modules.notebook.rules import Calendar, Schedule, transition
from app.modules.notebook.schemas import GroupBy, NotebookGroup, NotebookSummary
from app.modules.placement.models import answers
from app.modules.practice.models import sessions


async def calendar(db: AsyncSession) -> Calendar:
    values = dict(
        (
            await db.execute(
                select(content.remote_config).where(
                    content.remote_config.c.key.in_(("exam_date", "review_intervals_days"))
                )
            )
        )
        .tuples()
        .all()
    )
    if not values.get("exam_date") or not values.get("review_intervals_days"):
        raise ApiError(503, "service_unavailable", "Notebook configuration missing")
    return Calendar(
        date.fromisoformat(values["exam_date"]), tuple(values["review_intervals_days"])
    )


async def require_pass(db: AsyncSession, user: UUID, day: date) -> None:
    c = entitlements.c
    if not await db.scalar(
        select(c.user_id).where(
            c.user_id == user, c.kind == "season_pass", c.valid_until >= day
        )
    ):
        raise ApiError(403, "entitlement_required", "Review requires a season pass")


def schedule(row: RowMapping) -> Schedule:
    return Schedule(
        row["scheduled_on"], row["interval_index"], row["correct_streak"], row["due_on"]
    )


async def record(
    db: AsyncSession,
    user: UUID,
    key: str,
    question: str,
    answer: UUID,
    day: date,
    *,
    review: bool,
    correct: bool | None,
    config: Calendar | None = None,
) -> Schedule:
    cfg = config or await calendar(db)
    previous = (
        (
            await db.execute(
                select(entries).where(entries.c.user_id == user, entries.c.entry_key == key)
            )
        )
        .mappings()
        .one_or_none()
    )
    state = transition(
        cfg, day, schedule(previous) if previous else None, review=review, correct=correct
    )
    values = dict(
        **asdict(state),
        status="learned" if state.due_on is None else "open",
        last_answer_id=answer,
    )
    objective, _, misconception = key.partition("/")
    await db.execute(
        insert(entries)
        .values(
            user_id=user,
            entry_key=key,
            objective_id=objective,
            misconception_id=misconception or None,
            first_question_id=question,
            **values,
        )
        .on_conflict_do_update(index_elements=["user_id", "entry_key"], set_=values)
    )
    return state


@dataclass(frozen=True)
class Item:
    key: str
    objective: str
    first_question: str
    version: UUID
    topic: str
    topic_name: str
    misconception: str | None
    misconception_name: str | None
    subtest: str
    due: date | None

    def group(self, by: GroupBy) -> tuple[str, str | None]:
        if by == "topic":
            return self.topic, self.topic_name
        return self.misconception or "", self.misconception_name


async def read(db: AsyncSession, user: UUID, day: date, config: Calendar) -> list[Item]:
    o, t, m, s = (
        content.objectives,
        content.topics,
        content.misconceptions,
        content.subtests,
    )
    rows = (
        await db.execute(
            select(
                entries,
                t.c.id.label("topic"),
                t.c.name.label("topic_name"),
                m.c.text.label("misconception_name"),
                s.c.short_name.label("subtest"),
            )
            .select_from(
                entries.join(o)
                .join(t, o.c.topic_id == t.c.id)
                .join(s)
                .outerjoin(m, entries.c.misconception_id == m.c.id)
            )
            .where(entries.c.user_id == user)
        )
    ).mappings()
    items = [
        Item(
            r["entry_key"],
            r["objective_id"],
            r["first_question_id"],
            r["last_answer_id"],
            r["topic"],
            r["topic_name"],
            r["misconception_id"],
            r["misconception_name"],
            r["subtest"],
            schedule(r).effective_due(config, day),
        )
        for r in rows
    ]
    return sorted(items, key=lambda i: (i.due or date.max, i.key))


def summary(items: Sequence[Item], day: date, cfg: Calendar) -> NotebookSummary:
    dates = [i.due for i in items if i.due is not None]
    return NotebookSummary(
        open_count=len(dates),
        learned_count=len(items) - len(dates),
        due_today=sum(d <= day for d in dates),
        due_tomorrow=sum((d - day).days == 1 for d in dates),
        intervals=list(cfg.intervals(day)),
    )


def groups(items: Sequence[Item], day: date, by: GroupBy) -> list[NotebookGroup]:
    result: dict[str, NotebookGroup] = {}
    for item in items:
        key, name = item.group(by)
        group = result.setdefault(key, NotebookGroup(id=key, name=name, subtests=[]))
        if item.subtest not in group.subtests:
            group.subtests.append(item.subtest)
        if item.due is None:
            group.learned_count += 1
        else:
            group.open_count += 1
            if group.next_due_on is None or item.due < group.next_due_on:
                group.next_due_on = item.due
                group.next_due_days = max(0, (item.due - day).days)
    return sorted(
        result.values(), key=lambda g: (-g.open_count, g.next_due_on or date.max, g.id)
    )


async def merge(db: AsyncSession, source: UUID, target: UUID) -> None:
    for grant in (
        await db.execute(select(entitlements).where(entitlements.c.user_id == source))
    ).mappings():
        stmt = insert(entitlements).values({**grant, "user_id": target})
        await db.execute(
            stmt.on_conflict_do_update(
                index_elements=["user_id", "kind"],
                set_={
                    k: stmt.excluded[k] for k in ("valid_until", "source", "provider_ref")
                },
                where=stmt.excluded.valid_until > entitlements.c.valid_until,
            )
        )
    keys = list(
        await db.scalars(select(entries.c.entry_key).where(entries.c.user_id == source))
    )
    if not keys:
        return
    await db.execute(
        delete(entries).where(entries.c.user_id == target, entries.c.entry_key.in_(keys))
    )
    a = answers.c
    events = (
        await db.execute(
            select(answers, sessions.c.kind)
            .outerjoin(sessions, a.practice_id == sessions.c.id)
            .where(a.user_id == target, a.notebook_key.in_(keys))
            .order_by(a.answered_at, a.notebook_order)
        )
    ).mappings()
    cfg = await calendar(db)
    for event in events:
        await record(
            db,
            target,
            event["notebook_key"],
            event["question_id"],
            event["id"],
            event["answered_at"].astimezone(ISTANBUL).date(),
            review=event["kind"] == "review",
            correct=event["is_correct"],
            config=cfg,
        )
