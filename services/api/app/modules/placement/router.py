from uuid import UUID

from fastapi import APIRouter

from app.core.http import ApiError, ErrorBody, ServerTime, Session
from app.modules.accounts.security import CurrentUser
from app.modules.placement import service
from app.modules.placement.schemas import (
    Placement,
    PlacementResult,
    Start,
    Submission,
    WeekPreview,
)

router = APIRouter(
    tags=["Placement"],
    responses={
        401: {"model": ErrorBody},
        404: {"model": ErrorBody},
        409: {"model": ErrorBody},
        422: {"model": ErrorBody},
        503: {"model": ErrorBody},
    },
)


@router.post("/placement", operation_id="startPlacement")
async def start(
    data: Start, user: CurrentUser, session: Session, now: ServerTime
) -> Placement:
    result = await service.start(session, user, data.kind, now)
    await session.commit()
    return result


@router.post("/placement/{id}/answers", operation_id="answerPlacement")
async def answer(
    id: UUID, data: Submission, user: CurrentUser, session: Session, now: ServerTime
) -> Placement:
    result = await service.submit(session, user, id, data, now)
    await session.commit()
    return result


@router.get("/placement/{id}/result", operation_id="placementResult")
async def result(id: UUID, user: CurrentUser, session: Session) -> PlacementResult:
    return await service.result_for(session, user, id)


@router.get("/plan/first-week", operation_id="firstWeek")
async def first_week(user: CurrentUser, session: Session, now: ServerTime) -> WeekPreview:
    status = await service.placement_status(session, user, now)
    if status.latest_id is None:
        raise ApiError(404, "not_found", "No completed placement")
    return (await service.result_for(session, user, status.latest_id)).first_week
