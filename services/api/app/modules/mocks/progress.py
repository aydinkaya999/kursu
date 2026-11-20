from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.http import ISTANBUL
from app.modules.commerce.access import entitlement
from app.modules.content.models import subtests, topics
from app.modules.mocks.schemas import Progress, SectionProgress, TopicProgress
from app.modules.mocks.service import history
from app.modules.notebook.service import calendar
from app.modules.plan import evidence, rules
from app.modules.plan.schemas import NetRange
from app.modules.plan.service import sync_streak
from app.modules.practice.learning import mastery_state
from app.modules.practice.models import mastery


async def read(db: AsyncSession, user: UUID, now: datetime) -> Progress:
    day = now.astimezone(ISTANBUL).date()
    facts = await evidence.read(db, user, day, now, await evidence.history(db, user))
    stats, _ = await sync_streak(db, user, day)
    rows = (
        await db.execute(
            select(
                subtests.c.short_name,
                topics.c.name,
                mastery.c.value,
                mastery.c.answers_count,
            )
            .select_from(
                topics.join(subtests).outerjoin(
                    mastery,
                    and_(mastery.c.topic_id == topics.c.id, mastery.c.user_id == user),
                )
            )
            .order_by(subtests.c.exam_order, topics.c.name)
        )
    ).all()
    sections: dict[str, SectionProgress] = {}
    totals: dict[str, float] = {}
    for name, topic, value, count in rows:
        section = sections.setdefault(
            name, SectionProgress(name=name, mastery_percent=0, topics=[])
        )
        section.topics.append(
            TopicProgress(
                name=topic, state=mastery_state(value or 0, count or 0, value is not None)
            )
        )
        totals[name] = totals.get(name, 0) + (value or 0)
    for name, section in sections.items():
        section.mastery_percent = rules.half_up(100 * totals[name] / len(section.topics))
    detailed = (await entitlement(db, user, day)).active
    if not detailed:
        for section in sections.values():
            section.topics = []
    return Progress(
        days_to_exam=max(0, ((await calendar(db)).exam - day).days),
        net_range=NetRange(low=facts.net_range[0], high=facts.net_range[1])
        if facts.net_range
        else None,
        net_change=facts.net_change,
        trend=facts.trend if detailed and len(facts.trend) >= 2 else [],
        sections=list(sections.values()),
        history=await history(db, user) if detailed else [],
        streak=stats.current,
        weekly_done=stats.weekly_done,
        weekly_goal=rules.WEEKLY_GOAL,
        detailed=detailed,
    )
