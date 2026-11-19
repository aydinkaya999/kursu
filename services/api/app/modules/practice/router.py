from uuid import UUID

from fastapi import APIRouter

from app.core.http import ErrorBody, ServerTime, Session
from app.modules.accounts.security import CurrentUser
from app.modules.placement.schemas import Submission
from app.modules.placement.service import lock_user
from app.modules.practice import catalogue, moderation, service
from app.modules.practice.schemas import (
    Advance,
    CompleteLesson,
    Practice,
    PracticeStart,
    ReportInput,
    ReportReceipt,
    StudySection,
)

router = APIRouter(
    tags=["Study"], responses={code: {"model": ErrorBody} for code in (401, 404, 409, 422)}
)


@router.get("/study/lessons", operation_id="studyLibrary")
async def library(db: Session, user: CurrentUser) -> list[StudySection]:
    return await catalogue.library(db, user)


@router.post("/practice-sessions", operation_id="startPractice")
async def start(
    data: PracticeStart, db: Session, user: CurrentUser, now: ServerTime
) -> Practice:
    await lock_user(db, user)
    result = await service.start(db, user, data, now)
    await db.commit()
    return result


@router.get("/practice-sessions/{id}", operation_id="getPractice")
async def get_session(id: UUID, db: Session, user: CurrentUser) -> Practice:
    await lock_user(db, user)
    result = await service.presented(db, user, id)
    await db.commit()
    return result


@router.post("/practice-sessions/{id}/answers", operation_id="answerPractice")
async def answer(
    id: UUID, data: Submission, db: Session, user: CurrentUser, now: ServerTime
) -> Practice:
    await lock_user(db, user)
    result = await service.answer(db, user, id, data, now)
    await db.commit()
    return result


@router.post("/practice-sessions/{id}/advance", operation_id="advancePractice")
async def advance(id: UUID, data: Advance, db: Session, user: CurrentUser) -> Practice:
    await lock_user(db, user)
    result = await service.advance(db, user, id, data.question_id)
    await db.commit()
    return result


@router.post("/practice-sessions/{id}/finish", operation_id="finishPractice")
async def finish(id: UUID, db: Session, user: CurrentUser, now: ServerTime) -> Practice:
    await lock_user(db, user)
    result = await service.finish(db, user, id, now)
    await db.commit()
    return result


@router.post("/lessons/{id}/complete", operation_id="completeLesson")
async def complete_lesson(
    id: str, data: CompleteLesson, db: Session, user: CurrentUser, now: ServerTime
) -> Practice:
    await lock_user(db, user)
    result = await service.finish(db, user, data.session_id, now, id)
    await db.commit()
    return result


@router.post("/content-reports", operation_id="reportContent")
async def report(
    data: ReportInput, db: Session, user: CurrentUser, now: ServerTime
) -> ReportReceipt:
    result = await moderation.report(db, user, data, now)
    await db.commit()
    return result
