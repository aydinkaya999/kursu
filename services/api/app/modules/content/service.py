"""Catalogue queries and publication rules shared by the HTTP endpoints."""

from typing import Any

from pydantic import BaseModel
from sqlalchemy import ColumnElement, Select, Table, and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.content import models as db
from app.modules.content.schemas import LessonCard, LessonDetail, UnansweredQuestion


async def records[T: BaseModel](
    session: AsyncSession, statement: Select[Any], model: type[T]
) -> list[T]:
    rows = (await session.execute(statement)).mappings()
    return [model.model_validate(row) for row in rows]


def has_practice_feedback() -> ColumnElement[bool]:
    q = db.questions.c
    return and_(
        or_(q.subtest_id != "quantitative", func.jsonb_array_length(q.solution_steps) > 0),
        or_(
            q.subtest_id != "legislation",
            and_(q.source["kind"].astext == "law", q.source["quote"].astext.is_not(None)),
        ),
    )


def published_collection(
    parent: Table, links: Table, parent_key: str
) -> ColumnElement[bool]:
    hidden_question = (
        select(links.c.question_id)
        .join_from(links, db.questions)
        .where(
            links.c[parent_key] == parent.c.id,
            or_(db.questions.c.status != "published", ~has_practice_feedback()),
        )
        .exists()
    )
    return and_(parent.c.status == "published", ~hidden_question)


def lesson_catalogue() -> Select[Any]:
    lessons = db.lessons.c
    return select(
        lessons.id, lessons.topic_id, lessons.title, lessons.minutes, lessons.is_placeholder
    ).where(
        published_collection(db.lessons, db.lesson_check_questions, "lesson_id"),
        or_(
            lessons.source["kind"].astext != "law",
            lessons.source["quote"].astext.is_not(None),
        ),
    )


async def lesson_detail(session: AsyncSession, lesson_id: str) -> LessonDetail | None:
    # Read the header, ordered cards and checks from the same publication snapshot.
    await session.connection(execution_options={"isolation_level": "REPEATABLE READ"})
    detail_query = (
        lesson_catalogue()
        .join_from(db.lessons, db.topics)
        .join_from(db.topics, db.subtests)
        .add_columns(db.lessons.c.source, db.subtests.c.short_name.label("subtest"))
        .where(db.lessons.c.id == lesson_id)
    )
    header = (await session.execute(detail_query)).mappings().one_or_none()
    if header is None:
        return None

    cards = db.lesson_cards.c
    card_rows = await records(
        session,
        select(cards.position, cards.kind, cards.title, cards.blocks, cards.tip)
        .where(cards.lesson_id == lesson_id)
        .order_by(cards.position),
        LessonCard,
    )
    checks, q = db.lesson_check_questions, db.questions.c
    questions = await records(
        session,
        select(q.id, q.stem, q.options)
        .join_from(checks, db.questions)
        .where(checks.c.lesson_id == lesson_id)
        .order_by(checks.c.position),
        UnansweredQuestion,
    )
    return LessonDetail.model_validate(
        {**header, "cards": card_rows, "check_questions": questions}
    )


def mock_catalogue() -> Select[Any]:
    m = db.mock_exams.c
    return (
        select(m.id, m.title, m.published_at, m.is_placeholder)
        .where(published_collection(db.mock_exams, db.mock_exam_questions, "mock_exam_id"))
        .order_by(m.published_at.desc().nulls_last(), m.id)
    )
