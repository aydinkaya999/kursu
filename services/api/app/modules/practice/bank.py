from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.http import ApiError
from app.modules.content.models import questions
from app.modules.content.service import has_practice_feedback
from app.modules.placement.models import answers
from app.modules.placement.service import visible
from app.modules.practice.learning import difficulty
from app.modules.practice.models import mastery


def select_items(bank: Sequence[tuple[str, int]], base: int, count: int) -> list[str]:
    if len(bank) < count:
        raise ApiError(
            409, "content_unavailable", "Too few eligible questions for this topic"
        )
    remaining = list(bank)
    selected = []
    for index in range(count):
        level = base
        if index % 3 == 2:
            level = 2 if base != 2 else (1 if index % 6 == 2 else 3)
        item = min(remaining, key=lambda pair: abs(pair[1] - level))
        remaining.remove(item)
        selected.append(item[0])
    return selected


async def topic_questions(
    db: AsyncSession, user: UUID, topic: str, count: int
) -> list[str]:
    q = questions.c
    seen = select(answers.c.question_id).where(answers.c.user_id == user)
    rows = (
        (
            await db.execute(
                select(q.id, q.difficulty)
                .where(
                    q.topic_id == topic,
                    q.status.in_(visible(user)),
                    has_practice_feedback(),
                )
                .order_by(q.id.in_(seen), q.is_placeholder, q.id)
            )
        )
        .tuples()
        .all()
    )
    value = await db.scalar(
        select(mastery.c.value).where(
            mastery.c.user_id == user, mastery.c.topic_id == topic
        )
    )
    return select_items(rows, difficulty(value or 0), count)
