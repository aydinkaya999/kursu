from collections import Counter
from datetime import datetime, timedelta
from math import ceil
from uuid import UUID, uuid4

from sqlalchemy import insert, select, update
from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.http import ISTANBUL, ApiError
from app.modules.commerce import access
from app.modules.content import models as content
from app.modules.content.schemas import UnansweredQuestion
from app.modules.content.service import mock_catalogue
from app.modules.mocks.models import attempts, slots
from app.modules.mocks.schemas import (
    Attempt,
    History,
    Mode,
    Result,
    ReviewedQuestion,
    Save,
    SectionScore,
    Slot,
    WrongTopic,
)
from app.modules.notebook import service as notebook
from app.modules.notebook.rules import entry_key
from app.modules.placement.models import answers
from app.modules.placement.service import lock_user
from app.modules.plan.models import plans, tasks
from app.modules.plan.service import credit
from app.modules.practice.learning import refresh

DURATION = 110


async def questions(db: AsyncSession, attempt: UUID) -> list[RowMapping]:
    return list(
        (
            await db.execute(
                select(slots, content.questions.c.status)
                .join_from(slots, content.questions)
                .where(slots.c.attempt_id == attempt)
                .order_by(slots.c.position)
            )
        ).mappings()
    )


async def start(
    db: AsyncSession, user: UUID, exam: str, mode: Mode, now: datetime
) -> Attempt:
    await lock_user(db, user)
    existing = await db.scalar(
        select(attempts.c.id)
        .where(
            attempts.c.user_id == user,
            attempts.c.mock_exam_id == exam,
            attempts.c.mode == mode,
            attempts.c.submitted_at.is_(None),
        )
        .order_by(attempts.c.started_at.desc())
        .limit(1)
    )
    if existing:
        return await present(db, await current(db, user, existing, now), now)
    mock = (
        (await db.execute(mock_catalogue().where(content.mock_exams.c.id == exam)))
        .mappings()
        .one_or_none()
    )
    if mock is None:
        raise ApiError(404, "not_found", "Mock not available")
    links, q = content.mock_exam_questions, content.questions
    bank = (
        (
            await db.execute(
                select(
                    links.c.position,
                    q,
                    content.subtests.c.short_name.label("subtest"),
                    content.topics.c.name.label("topic"),
                )
                .join_from(links, q)
                .join_from(q, content.subtests, q.c.subtest_id == content.subtests.c.id)
                .join_from(q, content.topics, q.c.topic_id == content.topics.c.id)
                .where(links.c.mock_exam_id == exam, q.c.status == "published")
                .order_by(links.c.position)
            )
        )
        .mappings()
        .all()
    )
    if len(bank) != 80:
        raise ApiError(409, "content_unavailable", "Mock question bank incomplete")
    attempt = uuid4()
    await access.use(db, user, now, "mock_exams", str(attempt))
    row = (
        (
            await db.execute(
                insert(attempts)
                .values(
                    id=attempt,
                    user_id=user,
                    mock_exam_id=exam,
                    title=mock["title"],
                    mode=mode,
                    position=1,
                    started_at=now,
                    deadline_at=now + timedelta(minutes=DURATION)
                    if mode == "timed"
                    else None,
                )
                .returning(attempts)
            )
        )
        .mappings()
        .one()
    )
    await db.execute(
        insert(slots),
        [
            dict(
                attempt_id=attempt,
                position=item["position"],
                question_id=item["id"],
                snapshot=dict(item),
            )
            for item in bank
        ],
    )
    return await present(db, row, now)


def net(correct: int, wrong: int) -> float:
    return correct - wrong / 4


async def grade(db: AsyncSession, row: RowMapping, submitted: datetime) -> RowMapping:
    user, attempt = row["user_id"], row["id"]
    sections: dict[str, SectionScore] = {}
    wrong_topics: Counter[str] = Counter()
    withdrawn = 0
    day = submitted.astimezone(ISTANBUL).date()
    config = await notebook.calendar(db)
    for item in await questions(db, attempt):
        q = item["snapshot"]
        score = sections.setdefault(q["subtest"], SectionScore(name=q["subtest"]))
        if item["status"] != "published":
            withdrawn += 1
            continue
        choice = item["selected_option"]
        if choice is None:
            score.blank += 1
            continue
        right = choice == q["correct_option"]
        misconception = (
            q["rationales"][choice].get("misconception_id") if not right else None
        )
        key = entry_key(q["objective_id"], misconception) if not right else None
        if right:
            score.correct += 1
        else:
            score.wrong += 1
            wrong_topics[q["topic"]] += 1
        answer = uuid4()
        await db.execute(
            insert(answers).values(
                id=answer,
                user_id=user,
                mock_id=attempt,
                position=item["position"],
                question_id=q["id"],
                subtest_id=q["subtest_id"],
                topic_id=q["topic_id"],
                selected_option=choice,
                is_correct=right,
                not_sure=False,
                client_answer_id=answer,
                answered_at=submitted,
                misconception_id=misconception,
                notebook_key=key,
            )
        )
        if key:
            await notebook.record(
                db,
                user,
                key,
                q["id"],
                answer,
                day,
                review=False,
                correct=False,
                config=config,
            )
    for section in sections.values():
        section.net = net(section.correct, section.wrong)
    correct = sum(s.correct for s in sections.values())
    wrong = sum(s.wrong for s in sections.values())
    blank = sum(s.blank for s in sections.values())
    priorities = sorted(
        sections.values(), key=lambda s: s.net / max(1, s.correct + s.wrong + s.blank)
    )
    result = Result(
        id=attempt,
        title=row["title"],
        submitted_at=submitted,
        mode=row["mode"],
        used_minutes=ceil(max(0, (submitted - row["started_at"]).total_seconds()) / 60),
        duration_minutes=DURATION,
        total=correct + wrong + blank,
        withdrawn=withdrawn,
        correct=correct,
        wrong=wrong,
        blank=blank,
        net=net(correct, wrong),
        sections=list(sections.values()),
        priorities=[s.name for s in priorities[:2]],
        wrong_topics=[WrongTopic(name=k, count=v) for k, v in wrong_topics.most_common()],
    )
    await refresh(db, user)
    task = (
        await db.execute(
            select(tasks.c.id, tasks.c.plan_id)
            .join_from(tasks, plans)
            .where(
                plans.c.user_id == user,
                plans.c.plan_date == day,
                tasks.c.included,
                tasks.c.type == "mock",
                tasks.c.ref["content_id"].astext == row["mock_exam_id"],
                tasks.c.state != "done",
            )
            .limit(1)
        )
    ).one_or_none()
    if task:
        await db.execute(
            update(tasks)
            .where(tasks.c.id == task.id)
            .values(state="done", completed_at=submitted)
        )
        await credit(db, task.plan_id, submitted)
    return (
        (
            await db.execute(
                update(attempts)
                .where(attempts.c.id == attempt)
                .values(submitted_at=submitted, result=result.model_dump(mode="json"))
                .returning(attempts)
            )
        )
        .mappings()
        .one()
    )


async def current(db: AsyncSession, user: UUID, attempt: UUID, now: datetime) -> RowMapping:
    await lock_user(db, user)
    row = (
        (
            await db.execute(
                select(attempts)
                .where(attempts.c.user_id == user, attempts.c.id == attempt)
                .with_for_update()
            )
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        raise ApiError(404, "not_found", "Mock attempt not found")
    if row["submitted_at"] is None and row["deadline_at"] and row["deadline_at"] <= now:
        return await grade(db, row, row["deadline_at"])
    return row


async def present(db: AsyncSession, row: RowMapping, now: datetime) -> Attempt:
    items = [
        Slot(
            position=item["position"],
            subtest=item["snapshot"]["subtest"],
            question=UnansweredQuestion.model_validate(item["snapshot"])
            if item["status"] == "published"
            else None,
            selected_option=item["selected_option"]
            if item["status"] == "published"
            else None,
            flagged=item["flagged"],
        )
        for item in await questions(db, row["id"])
    ]
    remaining = (
        max(0, ceil((row["deadline_at"] - now).total_seconds()))
        if row["deadline_at"]
        else None
    )
    return Attempt(
        **dict(row),
        questions=items,
        blank=sum(s.question is not None and s.selected_option is None for s in items),
        remaining_seconds=remaining,
    )


async def save(
    db: AsyncSession, row: RowMapping, question_id: str, data: Save, now: datetime
) -> Attempt:
    if row["submitted_at"] is None:
        values = data.model_dump(exclude_unset=True)
        if values.get("flagged", False) is None or not values:
            raise ApiError(422, "validation_error", "Specify a choice or flag")
        eligible = select(content.questions.c.id).where(
            content.questions.c.status == "published"
        )
        changed = await db.scalar(
            update(slots)
            .where(
                slots.c.attempt_id == row["id"],
                slots.c.question_id == question_id,
                slots.c.question_id.in_(eligible),
            )
            .values(**values, updated_at=now)
            .returning(slots.c.position)
        )
        if changed is None:
            raise ApiError(404, "not_found", "Question not available")
    return await present(db, row, now)


def result(row: RowMapping) -> Result:
    if row["submitted_at"] is None:
        raise ApiError(409, "conflict", "Submit the mock before viewing feedback")
    return Result.model_validate(row["result"])


async def review(db: AsyncSession, row: RowMapping) -> list[ReviewedQuestion]:
    result(row)
    items = []
    for item in await questions(db, row["id"]):
        if item["status"] != "published":
            continue
        q, selected = item["snapshot"], item["selected_option"]
        order = dict.fromkeys([selected, q["correct_option"], *q["options"]])
        items.append(
            ReviewedQuestion.model_validate(
                dict(
                    position=item["position"],
                    question=q,
                    selected=selected,
                    correct=q["correct_option"],
                    rationales=[
                        dict(option=k, text=q["rationales"][k]["text"]) for k in order if k
                    ],
                    source=q["source"],
                    steps=q["solution_steps"],
                )
            )
        )
    return items


async def history(db: AsyncSession, user: UUID) -> list[History]:
    rows = (
        await db.execute(
            select(
                attempts.c.id,
                attempts.c.title,
                attempts.c.submitted_at,
                attempts.c.result["net"].as_float().label("net"),
            )
            .where(attempts.c.user_id == user, attempts.c.submitted_at.is_not(None))
            .order_by(attempts.c.submitted_at.desc(), attempts.c.id)
        )
    ).mappings()
    return [History.model_validate(r) for r in rows]


async def submit_expired(db: AsyncSession, now: datetime) -> int:
    due = (
        await db.execute(
            select(attempts.c.user_id, attempts.c.id)
            .where(attempts.c.submitted_at.is_(None), attempts.c.deadline_at <= now)
            .order_by(attempts.c.deadline_at)
        )
    ).all()
    count = 0
    for owner, attempt in due:
        await lock_user(db, owner)
        active = await db.scalar(
            select(attempts.c.id).where(
                attempts.c.id == attempt,
                attempts.c.user_id == owner,
                attempts.c.submitted_at.is_(None),
            )
        )
        if active:
            await current(db, owner, attempt, now)
            count += 1
        await db.commit()
    return count
