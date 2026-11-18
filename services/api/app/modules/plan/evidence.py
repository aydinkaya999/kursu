from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from fractions import Fraction
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.http import ISTANBUL
from app.modules.content import models as content
from app.modules.content.service import lesson_catalogue, mock_catalogue
from app.modules.placement.models import answers, attempts
from app.modules.placement.service import expected_net, range_for
from app.modules.plan.models import plans, tasks
from app.modules.plan.rules import DAY, Topic, half_up
from app.modules.plan.schemas import Priority


@dataclass
class Evidence:
    topics: list[Topic]
    due: list[str]
    mock: tuple[str, str] | None
    mock_ids: set[str]
    priorities: list[Priority]
    net_range: tuple[int, int] | None
    net_change: int | None


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
                a.not_sure,
                a.answered_at,
                q.objective_id,
            )
            .join_from(answers, content.questions)
            .where(a.user_id == user, a.answered_at <= now)
            .order_by(a.answered_at, a.id)
        )
    ).all()
    mastery: dict[str, float] = defaultdict(float)
    seen: set[str] = set()
    reviewed: dict[str, datetime] = {}
    read_lessons: set[str] = set()
    done_mocks: set[str] = set()
    lesson_events: list[tuple[datetime, str]] = []
    for item in work:
        ref = item["ref"]
        if item["state"] != "pending" and ref.get("topic_id"):
            seen.add(ref["topic_id"])
        if item["state"] != "done":
            continue
        if item["type"] == "review":
            for objective in ref["objectives"]:
                reviewed[objective] = max(
                    reviewed.get(objective, item["completed_at"]), item["completed_at"]
                )
        if item["type"] == "lesson":
            read_lessons.add(ref["content_id"])
            lesson_events.append((item["completed_at"], ref["topic_id"]))
        if item["type"] == "mock":
            done_mocks.add(ref["content_id"])
    earliest: dict[str, date] = {}
    events: list[tuple[datetime, str, float | None]] = [
        (ts, topic, None) for ts, topic in lesson_events
    ]
    for r in records:
        if r.selected_option is not None:
            seen.add(r.topic_id)
            x = (0.5 if r.not_sure else 1.0) if r.is_correct else 0.0
            events.append((r.answered_at, r.topic_id, x))
        if (r.is_correct is False or r.not_sure) and (
            r.objective_id not in reviewed or r.answered_at > reviewed[r.objective_id]
        ):
            due = r.answered_at.astimezone(ISTANBUL).date() + DAY
            if due <= day:
                earliest.setdefault(r.objective_id, due)
    for _, topic, outcome in sorted(events, key=lambda e: e[0]):
        mastery[topic] = (
            max(0.3, mastery[topic])
            if outcome is None
            else mastery[topic] + 0.2 * (outcome - mastery[topic])
        )
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
                .where(q.status == "published")
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
        m = mastery[t["id"]]
        values[t["subtest_id"]].append(m)
        topics.append(
            Topic(
                t["id"],
                t["name"],
                s["short_name"],
                s["weight_p1"],
                m,
                t["id"] in seen,
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
        sorted(earliest, key=lambda k: (earliest[k], k)),
        (mock["id"], mock["title"]) if mock else None,
        {m["id"] for m in rows},
        priorities,
        current_range,
        delta,
    )
