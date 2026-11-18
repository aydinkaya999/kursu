from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import Database

ISTANBUL = ZoneInfo("Europe/Istanbul")


def server_now() -> datetime:
    return datetime.now(UTC)


ServerTime = Annotated[datetime, Depends(server_now)]


async def session_for_request(request: Request) -> AsyncIterator[AsyncSession]:
    database: Database = request.app.state.database
    async with database.sessions() as session:
        yield session


Session = Annotated[AsyncSession, Depends(session_for_request)]


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, str]


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, **details: str):
        self.status = status
        self.body = ErrorBody(code=code, message=message, details=details)


async def handle_error(request: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, ApiError)
    return JSONResponse(status_code=error.status, content=error.body.model_dump())
