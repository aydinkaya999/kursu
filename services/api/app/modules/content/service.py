"""Catalogue queries and publication rules shared by the HTTP endpoints."""

from typing import Any

from pydantic import BaseModel
from sqlalchemy import ColumnElement, Select, Table, and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.content import models as db
from app.modules.content.schemas import LessonCard, LessonDetail, UnansweredQuestion


async def records[T: BaseModel](
    session: AsyncSession, statement: Select[Any], model: type[T]
) -> list[T]:
    rows = (await session.execute(statement)).mappings()
    return [model.model_validate(row) for row in rows]


def published_collection(
    parent: Table, links: Table, parent_key: str
) -> ColumnElement[bool]:
    hidden_question = (
        select(links.c.question_id)
        .join_from(links, db.questions)
        .where(links.c[parent_key] == parent.c.id, db.questions.c.status != "published")
        .exists()
    )
    return and_(parent.c.status == "published", ~hidden_question)


def lesson_catalogue() -> Select[Any]:
    lessons = db.lessons.c
    return select(
        lessons.id, lessons.topic_id, lessons.title, lessons.minutes, lessons.is_placeholder
    ).where(published_collection(db.lessons, db.lesson_check_questions, "lesson_id"))


async def lesson_detail(session: AsyncSession, lesson_id: str) -> LessonDetail | None:
    # Read the header, ordered cards and checks from the same publication snapshot.
    await session.connection(execution_options={"isolation_level": "REPEATABLE READ"})
    detail_query = (
        lesson_catalogue()
        .add_columns(db.lessons.c.source)
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
