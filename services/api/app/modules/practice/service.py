from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import func, insert, or_, select, update
from sqlalchemy.dialects.postgresql import insert as upsert
from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.http import ISTANBUL, ApiError
from app.modules.content import models as content
from app.modules.content.schemas import UnansweredQuestion
from app.modules.content.service import has_practice_feedback, lesson_catalogue
from app.modules.placement.models import answers
from app.modules.placement.schemas import Submission
from app.modules.placement.service import visible
from app.modules.plan import service as plan
from app.modules.plan.models import plans, tasks
from app.modules.practice import learning
from app.modules.practice.bank import topic_questions
from app.modules.practice.models import completions, sessions
from app.modules.practice.schemas import Feedback, Practice, PracticeStart


async def load(db: AsyncSession, user: UUID, key: UUID) -> RowMapping:
    row = (
        (
            await db.execute(
                select(sessions, content.subtests.c.short_name.label("subtest"))
                .join_from(sessions, content.topics)
                .join_from(content.topics, content.subtests)
                .where(sessions.c.id == key, sessions.c.user_id == user)
            )
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        raise ApiError(404, "not_found", "Practice session not found")
    return row


async def move(db: AsyncSession, row: RowMapping) -> None:
    last = row["position"] == len(row["question_ids"])
    await db.execute(
        update(sessions)
        .where(sessions.c.id == row["id"])
        .values(
            position=row["position"] if last else row["position"] + 1,
            state="ready" if last else "question",
        )
    )


async def lesson_checks(db: AsyncSession, lesson_id: str) -> list[str]:
    checks = content.lesson_check_questions.c
    published = lesson_catalogue().subquery()
    return list(
        await db.scalars(
            select(checks.question_id)
            .join_from(
                content.lesson_check_questions,
                published,
                published.c.id == checks.lesson_id,
            )
            .where(checks.lesson_id == lesson_id)
            .order_by(checks.position)
        )
    )


async def require_current_lesson(db: AsyncSession, row: RowMapping) -> None:
    lesson_id = row["lesson_id"]
    if lesson_id and await lesson_checks(db, lesson_id) != row["question_ids"]:
        raise ApiError(409, "content_unavailable", "The lesson or its checks have changed")


async def presented(db: AsyncSession, user: UUID, key: UUID) -> Practice:
    row = await load(db, user, key)
    ids = list(row["question_ids"])
    result = Practice.model_validate({**row, "total": len(ids)})
    if result.state in ("ready", "completed"):
        return result
    q = content.questions.c
    pos = result.position - 1
    await require_current_lesson(db, row)
    eligible = select(q.id, q.stem, q.options).where(
        q.status.in_(visible(user)), has_practice_feedback()
    )
    item = (await db.execute(eligible.where(q.id == ids[pos]))).mappings().one_or_none()
    if item is None:
        if result.state == "feedback":
            await move(db, row)
            return await presented(db, user, key)
        old_level = select(q.difficulty).where(q.id == ids[pos]).scalar_subquery()
        item = (
            (
                await db.execute(
                    eligible.where(q.topic_id == row["topic_id"], q.id.not_in(ids))
                    .order_by(func.abs(q.difficulty - old_level), q.is_placeholder, q.id)
                    .limit(1)
                )
            )
            .mappings()
            .one_or_none()
        )
        if item is None:
            raise ApiError(409, "content_unavailable", "No eligible replacement question")
        ids[pos] = item["id"]
        await db.execute(
            update(sessions).where(sessions.c.id == key).values(question_ids=ids)
        )
    if result.state == "question":
        result.question = UnansweredQuestion.model_validate(item)
    else:
        saved = await db.scalar(
            select(answers.c.feedback).where(
                answers.c.practice_id == key, answers.c.position == result.position
            )
        )
        result.feedback = Feedback.model_validate(saved)
        if row["lesson_id"] and not result.feedback.is_correct:
            checks = content.lesson_check_questions.c
            result.feedback.card_position = await db.scalar(
                select(checks.card_position).where(
                    checks.lesson_id == row["lesson_id"], checks.question_id == item["id"]
                )
            )
        ref = result.feedback.related_lesson_id
        if ref and not await db.scalar(
            lesson_catalogue().where(content.lessons.c.id == ref)
        ):
            result.feedback.related_lesson_id = None
            result.feedback.suggest_lesson = False
    return result


async def start(
    db: AsyncSession, user: UUID, data: PracticeStart, now: datetime
) -> Practice:
    lesson = data.kind == "lesson_check"
    topic_id = data.content_id
    task = None
    if data.task_id is not None:
        task = await plan.task_action(db, user, data.task_id, now, "start")
        if task.content_id != data.content_id or task.kind != (
            "lesson" if lesson else "topic_test"
        ):
            raise ApiError(409, "conflict", "Assignment does not match this activity")
    if lesson:
        header = (
            (
                await db.execute(
                    lesson_catalogue().where(content.lessons.c.id == data.content_id)
                )
            )
            .mappings()
            .one_or_none()
        )
        if not header:
            raise ApiError(404, "not_found", "Lesson unavailable")
        topic_id = header["topic_id"]
        ids = await lesson_checks(db, data.content_id)
        if len(ids) != 2:
            raise ApiError(409, "content_unavailable", "Lesson checks are incomplete")
    elif not await db.scalar(
        select(content.topics.c.id).where(content.topics.c.id == topic_id)
    ):
        raise ApiError(404, "not_found", "Topic not found")
    s = sessions.c
    resume = select(s.id).where(
        s.user_id == user,
        s.kind == data.kind,
        s.topic_id == topic_id,
        s.lesson_id == (data.content_id if lesson else None),
    )
    if lesson:
        resume = resume.where(s.question_ids == ids)
    if data.task_id:
        existing = await db.scalar(
            resume.where(s.task_id == data.task_id)
            .order_by((s.state == "completed").asc(), s.started_at.desc())
            .limit(1)
        )
        if existing:
            return await presented(db, user, existing)
    if task and not lesson:
        resume = resume.where(func.jsonb_array_length(s.question_ids) == task.count)
    if data.task_id:
        resume = resume.where(s.task_id.is_(None))
    existing = await db.scalar(
        resume.where(s.state != "completed").order_by(s.started_at.desc(), s.id).limit(1)
    )
    if existing:
        if data.task_id:
            await db.execute(
                update(sessions).where(s.id == existing).values(task_id=data.task_id)
            )
        return await presented(db, user, existing)
    if not lesson:
        ids = await topic_questions(db, user, topic_id, task.count if task else 10)
    key = uuid4()
    await db.execute(
        insert(sessions).values(
            id=key,
            user_id=user,
            kind=data.kind,
            topic_id=topic_id,
            lesson_id=data.content_id if lesson else None,
            task_id=data.task_id,
            question_ids=ids,
            position=1,
            state="question",
            started_at=now,
        )
    )
    return await presented(db, user, key)


async def make_feedback(
    db: AsyncSession, user: UUID, row: RowMapping, q: RowMapping, data: Submission
) -> Feedback:
    choice = data.selected_option
    assert choice is not None
    correct = q["correct_option"]
    options = list(dict.fromkeys([choice, correct, *"ABCDE"]))
    misconception = (
        q["rationales"][choice].get("misconception_id") if choice != correct else None
    )
    count = (
        await db.scalar(
            select(func.count())
            .select_from(answers)
            .where(answers.c.user_id == user, answers.c.misconception_id == misconception)
        )
        if misconception
        else 0
    )
    related = await db.scalar(
        lesson_catalogue()
        .where(
            or_(
                content.lessons.c.id == q["related_lesson_id"],
                content.lessons.c.topic_id == q["topic_id"],
            )
        )
        .order_by(
            (content.lessons.c.id == q["related_lesson_id"]).desc(),
            content.lessons.c.is_placeholder,
            content.lessons.c.id,
        )
        .limit(1)
    )
    checks = content.lesson_check_questions.c
    card = (
        await db.scalar(
            select(checks.card_position).where(
                checks.lesson_id == row["lesson_id"], checks.question_id == q["id"]
            )
        )
        if row["lesson_id"] and choice != correct
        else None
    )
    return Feedback.model_validate(
        dict(
            question=q,
            selected=choice,
            correct=correct,
            is_correct=choice == correct,
            rationales=[dict(option=o, text=q["rationales"][o]["text"]) for o in options],
            source=q["source"],
            steps=q["solution_steps"],
            misconception_count=count or 0,
            suggest_lesson=bool(related and count and count >= 3),
            related_lesson_id=related,
            card_position=card,
        )
    )


async def answer(
    db: AsyncSession, user: UUID, key: UUID, data: Submission, now: datetime
) -> Practice:
    row = await load(db, user, key)
    a = answers.c
    previous = (
        (
            await db.execute(
                select(answers).where(
                    a.user_id == user, a.client_answer_id == data.client_answer_id
                )
            )
        )
        .mappings()
        .one_or_none()
    )
    if previous:
        if (
            previous["practice_id"],
            previous["question_id"],
            previous["selected_option"],
            previous["not_sure"],
        ) != (key, data.question_id, data.selected_option, data.not_sure):
            raise ApiError(409, "conflict", "Answer ID already used for another submission")
        return await presented(db, user, key)
    if (
        row["state"] != "question"
        or row["question_ids"][row["position"] - 1] != data.question_id
    ):
        raise ApiError(409, "conflict", "Question is no longer current")
    q = (
        (
            await db.execute(
                select(content.questions)
                .where(
                    content.questions.c.id == data.question_id,
                    content.questions.c.status.in_(visible(user)),
                    has_practice_feedback(),
                )
                .with_for_update(read=True)
            )
        )
        .mappings()
        .one_or_none()
    )
    if q is None:
        raise ApiError(409, "content_unavailable", "Question withdrawn")
    await require_current_lesson(db, row)
    choice = data.selected_option
    correct = choice == q["correct_option"] if choice else None
    key_answer = uuid4()
    await db.execute(
        insert(answers).values(
            id=key_answer,
            user_id=user,
            practice_id=key,
            position=row["position"],
            topic_id=q["topic_id"],
            subtest_id=q["subtest_id"],
            is_correct=correct,
            misconception_id=q["rationales"][choice].get("misconception_id")
            if choice and correct is False
            else None,
            answered_at=now,
            **data.model_dump(),
        )
    )
    if choice:
        feedback = await make_feedback(db, user, row, q, data)
        await db.execute(
            update(answers)
            .where(a.id == key_answer)
            .values(feedback=feedback.model_dump(mode="json"))
        )
        await db.execute(
            update(sessions).where(sessions.c.id == key).values(state="feedback")
        )
        await learning.refresh(db, user, q["topic_id"])
    else:
        await move(db, row)
    return await presented(db, user, key)


async def advance(db: AsyncSession, user: UUID, key: UUID, question: str) -> Practice:
    row = await load(db, user, key)
    if row["state"] == "feedback" and row["question_ids"][row["position"] - 1] == question:
        await move(db, row)
    elif not await db.scalar(
        select(answers.c.id).where(
            answers.c.practice_id == key, answers.c.question_id == question
        )
    ):
        raise ApiError(409, "conflict", "Answer the current question first")
    return await presented(db, user, key)


async def finish(
    db: AsyncSession, user: UUID, key: UUID, now: datetime, lesson: str | None = None
) -> Practice:
    row = await load(db, user, key)
    if lesson is not None and lesson != row["lesson_id"]:
        raise ApiError(409, "conflict", "Lesson does not match this session")
    if row["state"] == "completed":
        return await presented(db, user, key)
    if row["state"] != "ready":
        raise ApiError(409, "conflict", "Finish all questions and feedback first")
    if row["lesson_id"]:
        await db.execute(
            upsert(completions)
            .values(user_id=user, lesson_id=row["lesson_id"], completed_at=now)
            .on_conflict_do_nothing()
        )
        await learning.refresh(db, user, row["topic_id"])
    await db.execute(
        update(sessions)
        .where(sessions.c.id == key)
        .values(state="completed", completed_at=now)
    )
    task_key = (
        "lesson:" + row["lesson_id"]
        if row["lesson_id"]
        else "topic_test:" + row["topic_id"]
    )
    current = (
        await db.execute(
            select(tasks.c.id, tasks.c.plan_id, tasks.c.ref)
            .join_from(tasks, plans)
            .where(
                plans.c.user_id == user,
                plans.c.plan_date == now.astimezone(ISTANBUL).date(),
                tasks.c.task_key == task_key,
                tasks.c.included,
                tasks.c.state != "done",
            )
        )
    ).one_or_none()
    if current and (
        row["lesson_id"]
        or len(row["question_ids"]) >= current.ref["count"]
        or current.id == row["task_id"]
    ):
        await db.execute(
            update(tasks)
            .where(tasks.c.id == current.id)
            .values(state="done", completed_at=now)
        )
        await plan.credit(db, current.plan_id, now)
    return await presented(db, user, key)
