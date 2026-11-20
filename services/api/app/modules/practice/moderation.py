from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.http import ApiError
from app.modules.content.models import questions
from app.modules.photos.models import solutions
from app.modules.placement.service import lock_user, visible
from app.modules.practice.models import reports
from app.modules.practice.schemas import PhotoReportInput, ReportInput, ReportReceipt


async def report(
    db: AsyncSession, user: UUID, data: ReportInput | PhotoReportInput, now: datetime
) -> ReportReceipt:
    await lock_user(db, user)
    if isinstance(data, PhotoReportInput):
        owned = await db.scalar(
            select(solutions.c.id)
            .where(
                solutions.c.id == data.photo_solution_id,
                solutions.c.user_id == user,
                solutions.c.expires_at > now,
            )
            .with_for_update(read=True)
        )
        if owned is None:
            raise ApiError(404, "not_found", "Photo unavailable")
        await db.execute(
            insert(reports)
            .values(
                user_id=user,
                photo_solution_id=owned,
                text=data.text,
                created_at=now,
            )
            .on_conflict_do_nothing()
        )
        return ReportReceipt(received=True)
    q = questions.c
    status = await db.scalar(
        select(q.status).where(q.id == data.question_id).with_for_update()
    )
    own = (reports.c.user_id == user, reports.c.question_id == data.question_id)
    if status not in visible(user):
        if await db.scalar(select(reports.c.question_id).where(*own)):
            return ReportReceipt(received=True)
        raise ApiError(404, "not_found", "Question unavailable")
    await db.execute(
        insert(reports)
        .values(user_id=user, question_id=data.question_id, text=data.text, created_at=now)
        .on_conflict_do_nothing()
    )
    total = await db.scalar(
        select(func.count())
        .select_from(reports)
        .where(reports.c.question_id == data.question_id)
    )
    if total is not None and total >= 3:
        await db.execute(
            update(questions).where(q.id == data.question_id).values(status="quarantined")
        )
    return ReportReceipt(received=True)
