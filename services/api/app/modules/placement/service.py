from collections import Counter
from collections.abc import Mapping
from datetime import datetime, timedelta
from fractions import Fraction
from math import floor
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, insert, select, update
from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.http import ISTANBUL, ApiError
from app.modules.accounts.models import profiles, users
from app.modules.accounts.schemas import PlacementStatus
from app.modules.content.models import questions, remote_config, subtests, topics
from app.modules.content.schemas import UnansweredQuestion
from app.modules.placement.models import answers, attempts
from app.modules.placement.schemas import (
    Breakdown,
    FocusTopic,
    Kind,
    Placement,
    PlacementResult,
    Submission,
    WeekPreview,
)
from app.modules.practice import learning

QUOTAS = {
    "full": {
        "education": 11,
        "verbal": 6,
        "quantitative": 6,
        "legislation": 3,
        "history": 2,
        "geography": 2,
    },
    "short": {
        "education": 3,
        "verbal": 2,
        "quantitative": 2,
        "legislation": 1,
        "history": 1,
        "geography": 1,
    },
}
RETAKE_DAYS = 14
HISTORY_DAYS = 28


def sequence(kind: Kind) -> list[str]:
    quotas = QUOTAS[kind]
    return [
        subtest
        for turn in range(max(quotas.values()))
        for subtest, n in quotas.items()
        if turn < n
    ]


def next_level(level: int, correct: bool | None) -> int:
    if correct is None:
        return level
    return max(1, min(3, level + (1 if correct else -1)))


def expected_net(
    exam_counts: Mapping[str, int], correct: Mapping[str, int], answered: Mapping[str, int]
) -> Fraction:
    value = Fraction()
    for subject, count in exam_counts.items():
        p = Fraction(correct.get(subject, 0) + 1, answered.get(subject, 0) + 2)
        value += count * (p - (1 - p) / 4)
    return value


def range_for(value: Fraction, ceiling: int) -> tuple[int, int]:
    spread = max(Fraction(3), value / 10)
    low, high = (
        max(0, min(ceiling, floor(v + Fraction(1, 2))))
        for v in (value - spread, value + spread)
    )
    return low, high


def estimate(
    exam_counts: Mapping[str, int], correct: Mapping[str, int], answered: Mapping[str, int]
) -> tuple[int, int]:
    return range_for(
        expected_net(exam_counts, correct, answered), sum(exam_counts.values())
    )


async def placement_status(
    session: AsyncSession, user: UUID, now: datetime
) -> PlacementStatus:
    a = attempts.c
    active = await session.scalar(
        select(a.id)
        .where(a.user_id == user, a.state.in_(("active", "paused")))
        .order_by((a.state == "active").desc(), a.started_at, a.id)
        .limit(1)
    )
    last = (
        await session.execute(
            select(a.id, a.completed_at)
            .where(a.user_id == user, a.state == "completed")
            .order_by(a.completed_at.desc())
            .limit(1)
        )
    ).one_or_none()
    due = (
        last.completed_at.astimezone(ISTANBUL).date() + timedelta(days=RETAKE_DAYS)
        if last
        else None
    )
    return PlacementStatus(
        active_id=active,
        latest_id=last.id if last else None,
        next_retake_on=due,
        can_retake=bool(due and now.astimezone(ISTANBUL).date() >= due and not active),
    )


def visible(user: UUID) -> tuple[str, ...]:
    return ("published", "prerelease") if user.int % 100 < 5 else ("published",)


async def find_question(
    session: AsyncSession, user: UUID, attempt_id: UUID, subject: str, level: int
) -> str:
    q, ans = questions.c, answers.c
    used = select(ans.question_id).where(ans.placement_id == attempt_id)
    seen = select(ans.question_id).where(ans.user_id == user)
    query = (
        select(q.id)
        .where(
            q.subtest_id == subject,
            q.status.in_(visible(user)),
            q.difficulty == level,
            q.id.not_in(used),
        )
        .order_by(q.id.in_(seen), q.is_placeholder, q.id)
        .limit(1)
    )
    chosen = await session.scalar(query)
    if chosen is None:
        raise ApiError(
            503, "content_unavailable", "No eligible placement question", subtest=subject
        )
    return str(chosen)


async def get_attempt(session: AsyncSession, user: UUID, attempt_id: UUID) -> RowMapping:
    row = (
        (
            await session.execute(
                select(attempts).where(
                    attempts.c.id == attempt_id, attempts.c.user_id == user
                )
            )
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        raise ApiError(404, "not_found", "Placement not found")
    return row


async def state(session: AsyncSession, user: UUID, attempt_id: UUID) -> Placement:
    row = await get_attempt(session, user, attempt_id)
    schedule = sequence(row["kind"])
    question = None
    name = None
    if row["state"] == "active":
        q = questions.c
        # A new content import can change an assigned question between visits.
        subject = schedule[row["position"] - 1]
        level = row["levels"][subject]
        query = (
            select(q.id, q.stem, q.options, subtests.c.name)
            .join(subtests, subtests.c.id == q.subtest_id)
            .where(
                q.status.in_(visible(user)), q.subtest_id == subject, q.difficulty == level
            )
        )
        data = (
            (await session.execute(query.where(q.id == row["current_question_id"])))
            .mappings()
            .one_or_none()
        )
        if data is None:
            replacement = await find_question(session, user, attempt_id, subject, level)
            await session.execute(
                update(attempts)
                .where(attempts.c.id == attempt_id)
                .values(current_question_id=replacement)
            )
            data = (
                (await session.execute(query.where(q.id == replacement))).mappings().one()
            )
        question = UnansweredQuestion.model_validate(data)
        name = data["name"]
    return Placement(
        id=attempt_id,
        kind=row["kind"],
        state=row["state"],
        position=row["position"],
        total=len(schedule),
        subtest=name,
        question=question,
    )


async def lock_user(session: AsyncSession, user: UUID) -> None:
    await session.execute(select(users.c.id).where(users.c.id == user).with_for_update())


async def start(session: AsyncSession, user: UUID, kind: Kind, now: datetime) -> Placement:
    await lock_user(session, user)
    if (
        await session.scalar(select(profiles.c.user_id).where(profiles.c.user_id == user))
        is None
    ):
        raise ApiError(409, "conflict", "Complete onboarding first")
    status = await placement_status(session, user, now)
    if status.active_id:
        await session.execute(
            update(attempts)
            .where(attempts.c.id == status.active_id, attempts.c.state == "paused")
            .values(state="active")
        )
        return await state(session, user, status.active_id)
    if kind == "full" and status.latest_id:
        return await state(session, user, status.latest_id)
    if kind == "short" and not status.can_retake:
        raise ApiError(409, "conflict", "Short placement is not available yet")
    attempt_id = uuid4()
    levels = dict.fromkeys(QUOTAS[kind], 2)
    question = await find_question(session, user, attempt_id, sequence(kind)[0], 2)
    await session.execute(
        insert(attempts).values(
            id=attempt_id,
            user_id=user,
            kind=kind,
            state="active",
            position=1,
            levels=levels,
            current_question_id=question,
            started_at=now,
        )
    )
    return await state(session, user, attempt_id)


async def finish_result(
    session: AsyncSession, user: UUID, row: RowMapping, now: datetime
) -> PlacementResult:
    a = answers.c
    records = (
        await session.execute(
            select(a.subtest_id, a.topic_id, a.selected_option, a.is_correct).where(
                a.placement_id == row["id"]
            )
        )
    ).all()
    asked = Counter(r.subtest_id for r in records)
    correct = Counter(r.subtest_id for r in records if r.is_correct)
    topic_asked = Counter((r.subtest_id, r.topic_id) for r in records)
    topic_correct = Counter((r.subtest_id, r.topic_id) for r in records if r.is_correct)
    sections = (
        (await session.execute(select(subtests).order_by(subtests.c.exam_order)))
        .mappings()
        .all()
    )
    counts = {s["id"]: s["question_count"] for s in sections}
    ranked = sorted(sections, key=lambda s: Fraction(correct[s["id"]], asked[s["id"]]))
    breakdown = [
        Breakdown(
            subtest_id=s["id"],
            name=s["name"],
            correct=correct[s["id"]],
            asked=asked[s["id"]],
            priority=i < 2,
        )
        for i, s in enumerate(ranked)
    ]
    topic_ids = {r.topic_id for r in records}
    candidates = {
        t["id"]: t
        for t in (await session.execute(select(topics).where(topics.c.id.in_(topic_ids))))
        .mappings()
        .all()
    }
    focus = []
    for section in ranked[:3]:
        pair = min(
            (key for key in topic_asked if key[0] == section["id"]),
            key=lambda k: (
                Fraction(topic_correct[k], topic_asked[k]),
                candidates[k[1]]["is_placeholder"],
                k[1],
            ),
        )
        focus.append(
            FocusTopic(subtest=section["short_name"], topic=candidates[pair[1]]["name"])
        )
    evidence = select(
        a.subtest_id,
        func.count(a.selected_option).label("answered"),
        func.count().filter(a.is_correct.is_(True)).label("correct"),
    ).where(a.user_id == user)
    if row["kind"] == "full":
        evidence = evidence.where(a.placement_id == row["id"])
    else:
        evidence = evidence.where(
            a.answered_at >= now - timedelta(days=HISTORY_DAYS), a.answered_at <= now
        )
    grouped = (await session.execute(evidence.group_by(a.subtest_id))).all()
    low, high = estimate(
        counts,
        {r.subtest_id: r.correct for r in grouped},
        {r.subtest_id: r.answered for r in grouped},
    )
    minutes = await session.scalar(
        select(profiles.c.daily_minutes).where(profiles.c.user_id == user)
    )
    mock_day = await session.scalar(
        select(remote_config.c.value).where(remote_config.c.key == "mock_day")
    )
    preview = WeekPreview.model_validate(
        {"daily_minutes": minutes, "topics": focus, "mock_day": mock_day}
    )
    return PlacementResult(
        id=row["id"],
        kind=row["kind"],
        total=sum(asked.values()),
        exam_questions=sum(counts.values()),
        net_low=low,
        net_high=high,
        subtests=breakdown,
        first_week=preview,
    )


async def submit(
    session: AsyncSession, user: UUID, attempt_id: UUID, data: Submission, now: datetime
) -> Placement:
    await lock_user(session, user)
    row = await get_attempt(session, user, attempt_id)
    a = answers.c
    previous = (
        (
            await session.execute(
                select(answers).where(
                    a.user_id == user, a.client_answer_id == data.client_answer_id
                )
            )
        )
        .mappings()
        .one_or_none()
    )
    if previous is not None:
        if (
            previous["placement_id"],
            previous["question_id"],
            previous["selected_option"],
            previous["not_sure"],
        ) != (attempt_id, data.question_id, data.selected_option, data.not_sure):
            raise ApiError(409, "conflict", "Answer ID is already in use")
        return await state(session, user, attempt_id)
    if row["state"] != "active" or data.question_id != row["current_question_id"]:
        raise ApiError(409, "conflict", "This question is no longer current")
    q = questions.c
    order = sequence(row["kind"])
    subject = order[row["position"] - 1]
    item = (
        await session.execute(
            select(q.subtest_id, q.topic_id, q.correct_option, q.rationales)
            .where(
                q.id == data.question_id,
                q.status.in_(visible(user)),
                q.subtest_id == subject,
                q.difficulty == row["levels"][subject],
            )
            .with_for_update(read=True)
        )
    ).one_or_none()
    if item is None:
        raise ApiError(409, "conflict", "The current question is no longer eligible")
    correct = (
        None
        if data.selected_option is None
        else data.selected_option == item.correct_option
    )
    await session.execute(
        insert(answers).values(
            id=uuid4(),
            user_id=user,
            placement_id=attempt_id,
            position=row["position"],
            subtest_id=item.subtest_id,
            topic_id=item.topic_id,
            is_correct=correct,
            misconception_id=item.rationales[data.selected_option].get("misconception_id")
            if correct is False and data.selected_option
            else None,
            answered_at=now,
            **data.model_dump(),
        )
    )
    levels = dict(row["levels"])
    if correct is not None:
        await learning.refresh(session, user, item.topic_id)
    levels[item.subtest_id] = next_level(levels[item.subtest_id], correct)
    changes: dict[str, Any] = {"levels": levels}
    if row["position"] == len(order):
        result = await finish_result(session, user, row, now)
        changes.update(
            state="completed",
            completed_at=now,
            current_question_id=None,
            result=result.model_dump(mode="json"),
        )
    else:
        subject = order[row["position"]]
        question = await find_question(session, user, attempt_id, subject, levels[subject])
        changes.update(position=row["position"] + 1, current_question_id=question)
    await session.execute(
        update(attempts).where(attempts.c.id == attempt_id).values(**changes)
    )
    return await state(session, user, attempt_id)


async def result_for(
    session: AsyncSession, user: UUID, attempt_id: UUID
) -> PlacementResult:
    row = await get_attempt(session, user, attempt_id)
    if row["state"] != "completed":
        raise ApiError(409, "conflict", "Placement is still active")
    return PlacementResult.model_validate(row["result"])
