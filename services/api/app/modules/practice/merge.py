from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.practice import learning
from app.modules.practice.models import completions, reports, sessions


async def merge_study(db: AsyncSession, source: UUID, target: UUID) -> None:
    await db.execute(
        update(sessions).where(sessions.c.user_id == source).values(user_id=target)
    )
    for row in (
        await db.execute(select(completions).where(completions.c.user_id == source))
    ).mappings():
        stmt = insert(completions).values(
            user_id=target, lesson_id=row["lesson_id"], completed_at=row["completed_at"]
        )
        await db.execute(
            stmt.on_conflict_do_update(
                index_elements=["user_id", "lesson_id"],
                set_={
                    "completed_at": func.least(
                        completions.c.completed_at, stmt.excluded.completed_at
                    )
                },
            )
        )
    for row in (
        await db.execute(select(reports).where(reports.c.user_id == source))
    ).mappings():
        await db.execute(
            insert(reports)
            .values(
                user_id=target,
                question_id=row["question_id"],
                photo_solution_id=row["photo_solution_id"],
                text=row["text"],
                created_at=row["created_at"],
            )
            .on_conflict_do_nothing()
        )
    await learning.refresh(db, target)
