from uuid import UUID

from fastapi import APIRouter

from app.core.http import ErrorBody, ServerTime, Session
from app.modules.accounts.security import CurrentUser
from app.modules.plan import service
from app.modules.plan.schemas import PlanTask, Today

router = APIRouter(
    tags=["Daily plan"],
    responses={
        401: {"model": ErrorBody},
        404: {"model": ErrorBody},
        409: {"model": ErrorBody},
        503: {"model": ErrorBody},
    },
)


@router.get("/plan/today", operation_id="getToday")
async def today(user: CurrentUser, db: Session, now: ServerTime) -> Today:
    result = await service.today(db, user, now)
    await db.commit()
    return result


@router.get("/plan/tasks/{id}", operation_id="getPlanTask")
async def read_task(id: UUID, user: CurrentUser, db: Session, now: ServerTime) -> PlanTask:
    return await service.task_action(db, user, id, now, None)


@router.post("/plan/tasks/{id}/start", operation_id="startTask")
async def start_task(id: UUID, user: CurrentUser, db: Session, now: ServerTime) -> PlanTask:
    result = await service.task_action(db, user, id, now, "start")
    await db.commit()
    return result


@router.post("/plan/tasks/{id}/complete", operation_id="completeTask")
async def complete_task(
    id: UUID, user: CurrentUser, db: Session, now: ServerTime
) -> PlanTask:
    result = await service.task_action(db, user, id, now, "complete")
    await db.commit()
    return result
