from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response

from app.core.http import ErrorBody, ServerTime, Session
from app.modules.accounts.security import CurrentUser
from app.modules.commerce.access import settings
from app.modules.photos import service
from app.modules.photos.schemas import PhotoPolicy, PhotoQuota, PhotoSolution, PhotoUpload
from app.modules.photos.solver import VisionSolver, vision_solver
from app.modules.photos.storage import PhotoStore
from app.modules.photos.upload import PhotoRoute


def private_response(response: Response) -> None:
    response.headers["Cache-Control"] = "private, no-store"


router = APIRouter(
    prefix="/photo-solutions",
    route_class=PhotoRoute,
    tags=["Photo solve"],
    dependencies=[Depends(private_response)],
    responses={code: {"model": ErrorBody} for code in (401, 403, 404, 413, 422, 503)},
)


def photo_store(request: Request) -> PhotoStore:
    return PhotoStore(request.app.state.settings.photo_storage_dir)


Store = Annotated[PhotoStore, Depends(photo_store)]
Solver = Annotated[VisionSolver, Depends(vision_solver)]


@router.get("/quota", operation_id="getPhotoQuota")
async def quota(db: Session, user: CurrentUser, now: ServerTime) -> PhotoQuota:
    cfg = await settings(db, PhotoPolicy)
    result, _ = await service.allowance(db, user, now, cfg.photo_limits)
    return result


@router.post("", operation_id="solvePhoto")
async def upload(
    data: PhotoUpload,
    db: Session,
    user: CurrentUser,
    now: ServerTime,
    store: Store,
    solver: Solver,
) -> PhotoSolution:
    return await service.create(db, store, solver, user, data, now)


@router.get("/{id}", operation_id="getPhotoSolution")
async def solution(
    id: UUID, db: Session, user: CurrentUser, now: ServerTime, store: Store
) -> PhotoSolution:
    return await service.read(db, store, user, id, now)
