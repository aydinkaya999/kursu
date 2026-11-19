from collections import defaultdict
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.content import models as content
from app.modules.content.service import has_practice_feedback, lesson_catalogue
from app.modules.placement.service import visible
from app.modules.practice.learning import mastery_state
from app.modules.practice.models import completions, mastery
from app.modules.practice.schemas import StudyLesson, StudySection, StudyTopic


async def library(db: AsyncSession, user: UUID) -> list[StudySection]:
    done = select(completions.c.lesson_id).where(completions.c.user_id == user)
    items: dict[str, list[StudyLesson]] = defaultdict(list)
    for row in (
        await db.execute(
            lesson_catalogue()
            .add_columns(content.lessons.c.id.in_(done).label("completed"))
            .order_by(content.lessons.c.is_placeholder, content.lessons.c.title)
        )
    ).mappings():
        items[row["topic_id"]].append(StudyLesson.model_validate(row))
    counts = dict(
        (
            await db.execute(
                select(content.questions.c.topic_id, func.count())
                .where(
                    content.questions.c.status.in_(visible(user)), has_practice_feedback()
                )
                .group_by(content.questions.c.topic_id)
            )
        )
        .tuples()
        .all()
    )
    stats = {
        r.topic_id: r
        for r in await db.execute(select(mastery).where(mastery.c.user_id == user))
    }
    sections: dict[str, list[StudyTopic]] = defaultdict(list)
    for topic in await db.execute(
        select(content.topics, content.subtests.c.name.label("section"))
        .join_from(content.topics, content.subtests)
        .order_by(
            content.subtests.c.exam_order,
            content.topics.c.is_placeholder,
            content.topics.c.name,
        )
    ):
        entries = items[topic.id]
        if not entries and counts.get(topic.id, 0) < 10:
            continue
        record = stats.get(topic.id)
        sections[topic.section].append(
            StudyTopic(
                id=topic.id,
                name=topic.name,
                mastery=mastery_state(
                    record.value if record else 0,
                    record.answers_count if record else 0,
                    record is not None,
                ),
                can_practice=counts.get(topic.id, 0) >= 10,
                lessons=entries,
            )
        )
    return [StudySection(name=name, topics=topics) for name, topics in sections.items()]
