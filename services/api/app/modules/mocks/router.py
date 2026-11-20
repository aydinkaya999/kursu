from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import update

from app.core.http import ErrorBody, ServerTime, Session
from app.modules.accounts.security import CurrentUser
from app.modules.mocks import progress, service
from app.modules.mocks.models import attempts
from app.modules.mocks.schemas import (
    Attempt,
    History,
    Position,
    Progress,
    Result,
    ReviewedQuestion,
    Save,
    Start,
)
from app.modules.placement.service import lock_user

router = APIRouter(
    tags=["Mocks and progress"],
    responses={code: {"model": ErrorBody} for code in (401, 403, 404, 409, 422)},
)


@router.post("/mocks/{id}/attempts", operation_id="startMock")
async def start(
    id: str, data: Start, db: Session, user: CurrentUser, now: ServerTime
) -> Attempt:
    state = await service.start(db, user, id, data.mode, now)
    await db.commit()
    return state


@router.get("/mock-attempts/{id}", operation_id="getMockAttempt")
async def get(id: UUID, db: Session, user: CurrentUser, now: ServerTime) -> Attempt:
    state = await service.present(db, await service.current(db, user, id, now), now)
    await db.commit()
    return state


@router.put("/mock-attempts/{id}/answers/{question_id}", operation_id="saveMockAnswer")
async def save(
    id: UUID, question_id: str, data: Save, db: Session, user: CurrentUser, now: ServerTime
) -> Attempt:
    state = await service.save(
        db, await service.current(db, user, id, now), question_id, data, now
    )
    await db.commit()
    return state


@router.put("/mock-attempts/{id}/position", operation_id="moveMock")
async def move(
    id: UUID, data: Position, db: Session, user: CurrentUser, now: ServerTime
) -> Attempt:
    row = await service.current(db, user, id, now)
    if row["submitted_at"] is None:
        row = (
            (
                await db.execute(
                    update(attempts)
                    .where(attempts.c.id == id)
                    .values(position=data.position)
                    .returning(attempts)
                )
            )
            .mappings()
            .one()
        )
    state = await service.present(db, row, now)
    await db.commit()
    return state


@router.post("/mock-attempts/{id}/submit", operation_id="submitMock")
async def submit(id: UUID, db: Session, user: CurrentUser, now: ServerTime) -> Result:
    row = await service.current(db, user, id, now)
    if row["submitted_at"] is None:
        row = await service.grade(db, row, now)
    await db.commit()
    return service.result(row)


@router.get("/mock-attempts/{id}/result", operation_id="mockResult")
async def result(id: UUID, db: Session, user: CurrentUser, now: ServerTime) -> Result:
    data = service.result(await service.current(db, user, id, now))
    await db.commit()
    return data


@router.get("/mock-attempts/{id}/review", operation_id="mockReview")
async def review(
    id: UUID, db: Session, user: CurrentUser, now: ServerTime
) -> list[ReviewedQuestion]:
    data = await service.review(db, await service.current(db, user, id, now))
    await db.commit()
    return data


@router.get("/mock-history", operation_id="mockHistory")
async def history(db: Session, user: CurrentUser) -> list[History]:
    return await service.history(db, user)


@router.get("/progress", operation_id="getProgress")
async def get_progress(db: Session, user: CurrentUser, now: ServerTime) -> Progress:
    await lock_user(db, user)
    data = await progress.read(db, user, now)
    await db.commit()
    return data
