from typing import TYPE_CHECKING

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.modules.system.schemas import Health, ServiceUnavailable

if TYPE_CHECKING:
    from app.core.db import Database

router = APIRouter()


@router.get(
    "/health",
    operation_id="getHealth",
    response_model=Health,
    responses={503: {"model": ServiceUnavailable, "description": "Database unavailable"}},
)
async def health(request: Request) -> Health | JSONResponse:
    database: Database = request.app.state.database
    if await database.is_ready():
        return Health(status="ok")
    error = ServiceUnavailable(
        code="service_unavailable", message="Database unavailable", details={}
    )
    return JSONResponse(status_code=503, content=error.model_dump())
