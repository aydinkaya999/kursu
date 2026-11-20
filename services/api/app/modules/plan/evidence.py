from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from fractions import Fraction
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.http import ISTANBUL
from app.modules.content import models as content
from app.modules.content.service import (
    has_practice_feedback,
    lesson_catalogue,
    mock_catalogue,
)
from app.modules.mocks.models import attempts as mock_attempts
from app.modules.notebook import reviews
from app.modules.notebook import service as notebook
from app.modules.placement.models import answers, attempts
from app.modules.placement.service import expected_net, range_for
from app.modules.plan.models import plans, tasks
from app.modules.plan.rules import DAY, Topic, half_up
from app.modules.plan.schemas import Priority
from app.modules.practice.models import completions, sessions
from app.modules.practice.models import mastery as topic_mastery


@dataclass
class Evidence:
    topics: list[Topic]
    due: list[str]
    mock: tuple[str, str] | None
    mock_ids: set[str]
    priorities: list[Priority]
    net_range: tuple[int, int] | None
    net_change: int | None
    trend: list[float]


async def history(db: AsyncSession, user: UUID) -> list[RowMapping]:
    return list(
        (
            await db.execute(
                select(tasks, plans.c.plan_date)
                .join_from(tasks, plans)
                .where(plans.c.user_id == user)
                .order_by(plans.c.plan_date, tasks.c.position, tasks.c.id)
            )
        ).mappings()
    )


async def graded_today(db: AsyncSession, user: UUID, day: date) -> set[str]:
    start = datetime.combine(day, time.min, ISTANBUL)
    return set(
        await db.scalars(
            select(answers.c.notebook_key)
            .join_from(answers, sessions)
            .where(
                answers.c.user_id == user,
                sessions.c.kind == "review",
                answers.c.is_correct.is_not(None),
                answers.c.notebook_key.is_not(None),
                answers.c.answered_at >= start,
                answers.c.answered_at < start + DAY,
            )
        )
    )


async def due_entries(
    db: AsyncSession, user: UUID, day: date, work: list[RowMapping]
) -> list[str]:
    items = await notebook.read(db, user, day, await notebook.calendar(db))
    due = [i for i in items if i.due and i.due <= day]
    candidates = await reviews.bank(db, user, {i.objective for i in due})
    keys = [
        i.key for i in due if reviews.sibling(candidates[i.objective], i.first_question)
    ]
    current = next(
        (
            t
            for t in work
            if t["plan_date"] == day and t["type"] == "review" and t["included"]
        ),
        None,
    )
    if current:
        # Keep the assigned order and partial credit during a same-day rebuild.
        counted = await graded_today(db, user, day)
        assigned = [
            k for k in current["ref"].get("entry_keys", []) if k in counted or k in keys
        ]
        return list(dict.fromkeys([*assigned, *keys]))
    return keys


async def read(
    db: AsyncSession, user: UUID, day: date, now: datetime, work: list[RowMapping]
) -> Evidence:
    a, q = answers.c, content.questions.c
    records = (
        await db.execute(
            select(
                a.topic_id,
                a.subtest_id,
                a.selected_option,
                a.is_correct,
                a.answered_at,
            )
            .where(a.user_id == user, a.answered_at <= now)
            .order_by(a.answered_at, a.id)
        )
    ).all()
    mastery = dict(
        (
            await db.execute(
                select(topic_mastery.c.topic_id, topic_mastery.c.value).where(
                    topic_mastery.c.user_id == user
                )
            )
        )
        .tuples()
        .all()
    )
    seen: set[str] = set()
    read_lessons = set(
        await db.scalars(
            select(completions.c.lesson_id).where(completions.c.user_id == user)
        )
    )
    done_mocks = set(
        await db.scalars(
            select(mock_attempts.c.mock_exam_id).where(
                mock_attempts.c.user_id == user, mock_attempts.c.submitted_at.is_not(None)
            )
        )
    )
    for item in work:
        ref = item["ref"]
        if item["state"] != "pending" and ref.get("topic_id"):
            seen.add(ref["topic_id"])
        if item["state"] != "done":
            continue
        if item["type"] == "lesson":
            read_lessons.add(ref["content_id"])
        if item["type"] == "mock":
            done_mocks.add(ref["content_id"])
    for r in records:
        if r.selected_option is not None:
            seen.add(r.topic_id)
    subtests = (
        (await db.execute(select(content.subtests).order_by(content.subtests.c.exam_order)))
        .mappings()
        .all()
    )
    sections = {s["id"]: s for s in subtests}
    lesson_rows = (
        await db.execute(
            lesson_catalogue()
            .order_by(None)
            .order_by(content.lessons.c.is_placeholder, content.lessons.c.id)
        )
    ).mappings()
    lessons: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for lesson in lesson_rows:
        if lesson["id"] not in read_lessons:
            lessons[lesson["topic_id"]].append((lesson["id"], lesson["title"]))
    question_counts = dict(
        (
            await db.execute(
                select(q.topic_id, func.count())
                .where(q.status == "published", has_practice_feedback())
                .group_by(q.topic_id)
            )
        )
        .tuples()
        .all()
    )
    topics = []
    values: dict[str, list[float]] = defaultdict(list)
    for t in (
        await db.execute(select(content.topics).order_by(content.topics.c.id))
    ).mappings():
        s = sections[t["subtest_id"]]
        m = mastery.get(t["id"], 0.0)
        values[t["subtest_id"]].append(m)
        topics.append(
            Topic(
                t["id"],
                t["name"],
                s["short_name"],
                s["weight_p1"],
                m,
                t["id"] in seen or t["id"] in mastery,
                lessons[t["id"]],
                question_counts.get(t["id"], 0),
            )
        )
    means = {s["id"]: sum(values[s["id"]]) / max(1, len(values[s["id"]])) for s in subtests}
    priorities = [
        Priority(name=s["name"], mastery_percent=half_up(means[s["id"]] * 100))
        for s in sorted(subtests, key=lambda s: means[s["id"]])[:3]
    ]
    rows = (await db.execute(mock_catalogue())).mappings().all()
    mock = next((m for m in rows if m["id"] not in done_mocks), rows[0] if rows else None)
    counts = {s["id"]: s["question_count"] for s in subtests}

    def net(start: datetime, end: datetime) -> Fraction | None:
        period = [r for r in records if start < r.answered_at <= end]
        if not period:
            return None
        return expected_net(
            counts,
            Counter(r.subtest_id for r in period if r.is_correct),
            Counter(r.subtest_id for r in period if r.selected_option is not None),
        )

    recent = net(now - timedelta(days=28), now)
    previous = net(now - timedelta(days=56), now - timedelta(days=28))
    completed = await db.scalar(
        select(attempts.c.id)
        .where(attempts.c.user_id == user, attempts.c.state == "completed")
        .limit(1)
    )
    completed = completed or bool(done_mocks)
    current_range = (
        range_for(
            recent if recent is not None else expected_net(counts, {}, {}),
            sum(counts.values()),
        )
        if completed
        else None
    )
    delta = (
        half_up(float(recent - previous))
        if completed and recent is not None and previous is not None
        else None
    )
    return Evidence(
        topics,
        await due_entries(db, user, day, work),
        (mock["id"], mock["title"]) if mock else None,
        {m["id"] for m in rows},
        priorities,
        current_range,
        delta,
        [
            float(value)
            for week in range(4, 0, -1)
            if (value := net(now - timedelta(weeks=week), now - timedelta(weeks=week - 1)))
            is not None
        ],
    )
