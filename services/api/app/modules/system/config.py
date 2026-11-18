from datetime import date, datetime, time, timedelta
from math import ceil

from fastapi import APIRouter, Response
from pydantic import BaseModel
from sqlalchemy import select

from app.core.http import ISTANBUL, ApiError, ServerTime, Session
from app.modules.content.models import remote_config

router = APIRouter(tags=["System"])


class PublicConfig(BaseModel):
    app_name: str
    exam_date: date
    results_date: date
    server_now: datetime
    days_to_exam: int
    seconds_to_midnight: int


def countdown(exam: date, now: datetime) -> tuple[int, int]:
    local = now.astimezone(ISTANBUL)
    tomorrow = datetime.combine(local.date() + timedelta(days=1), time.min, ISTANBUL)
    return max(0, (exam - local.date()).days), ceil((tomorrow - local).total_seconds())


@router.get("/config", operation_id="getConfig")
async def read_config(
    response: Response, session: Session, now: ServerTime
) -> PublicConfig:
    response.headers["Cache-Control"] = "no-store"
    keys = ("app_name", "exam_date", "results_date")
    values = dict(
        (await session.execute(select(remote_config).where(remote_config.c.key.in_(keys))))
        .tuples()
        .all()
    )
    if any(key not in values for key in keys):
        raise ApiError(503, "service_unavailable", "Exam configuration is missing")
    exam = date.fromisoformat(values["exam_date"])
    days, seconds = countdown(exam, now)
    return PublicConfig(
        app_name=values["app_name"],
        exam_date=exam,
        results_date=date.fromisoformat(values["results_date"]),
        server_now=now,
        days_to_exam=days,
        seconds_to_midnight=seconds,
    )
