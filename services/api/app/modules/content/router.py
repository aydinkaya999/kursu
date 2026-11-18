from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import Database
from app.modules.content import models as db
from app.modules.content.schemas import (
    LessonDetail,
    LessonSummary,
    MockSummary,
    NotFound,
    Subtest,
    TeachingField,
    Topic,
)
from app.modules.content.service import (
    lesson_catalogue,
    lesson_detail,
    mock_catalogue,
    records,
)

router = APIRouter(tags=["Catalogue"])


async def session_for_request(request: Request) -> AsyncIterator[AsyncSession]:
    database: Database = request.app.state.database
    async with database.sessions() as session:
        yield session


Session = Annotated[AsyncSession, Depends(session_for_request)]


@router.get("/fields", operation_id="listFields")
async def list_fields(session: Session) -> list[TeachingField]:
    return await records(session, select(db.fields).order_by(db.fields.c.id), TeachingField)


@router.get("/subtests", operation_id="listSubtests")
async def list_subtests(session: Session) -> list[Subtest]:
    return await records(
        session, select(db.subtests).order_by(db.subtests.c.exam_order), Subtest
    )


@router.get("/topics", operation_id="listTopics")
async def list_topics(session: Session, subtest_id: str | None = None) -> list[Topic]:
    statement = select(db.topics).order_by(db.topics.c.id)
    if subtest_id is not None:
        statement = statement.where(db.topics.c.subtest_id == subtest_id)
    return await records(session, statement, Topic)


@router.get("/lessons", operation_id="listLessons")
async def list_lessons(
    session: Session, topic_id: str | None = None
) -> list[LessonSummary]:
    statement = lesson_catalogue().order_by(db.lessons.c.id)
    if topic_id is not None:
        statement = statement.where(db.lessons.c.topic_id == topic_id)
    return await records(session, statement, LessonSummary)


@router.get(
    "/lessons/{id}",
    operation_id="getLesson",
    response_model=LessonDetail,
    response_model_exclude_unset=True,
    responses={404: {"model": NotFound}},
)
async def get_lesson(id: str, session: Session) -> LessonDetail | JSONResponse:
    lesson = await lesson_detail(session, id)
    if lesson is None:
        error = NotFound(code="not_found", message="Lesson not found", details={})
        return JSONResponse(status_code=404, content=error.model_dump())
    return lesson


@router.get("/mocks", operation_id="listMocks")
async def list_mocks(session: Session) -> list[MockSummary]:
    return await records(session, mock_catalogue(), MockSummary)
