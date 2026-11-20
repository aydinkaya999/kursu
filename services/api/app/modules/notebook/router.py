from fastapi import APIRouter

from app.core.http import ISTANBUL, ErrorBody, ServerTime, Session
from app.modules.accounts.security import CurrentUser
from app.modules.notebook import service
from app.modules.notebook.schemas import GroupBy, NotebookGroup, NotebookSummary

router = APIRouter(tags=["Notebook"], responses={401: {"model": ErrorBody}})


@router.get("/notebook", operation_id="getNotebook")
async def notebook(
    db: Session, user: CurrentUser, now: ServerTime, group_by: GroupBy = "topic"
) -> list[NotebookGroup]:
    day = now.astimezone(ISTANBUL).date()
    return service.groups(
        await service.read(db, user, day, await service.calendar(db)), day, group_by
    )


@router.get("/notebook/summary", operation_id="notebookSummary")
async def summary(db: Session, user: CurrentUser, now: ServerTime) -> NotebookSummary:
    day = now.astimezone(ISTANBUL).date()
    cfg = await service.calendar(db)
    return service.summary(await service.read(db, user, day, cfg), day, cfg)
