from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import insert, select, update
from sqlalchemy.dialects.postgresql import insert as upsert
from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.http import ISTANBUL, ApiError
from app.modules.accounts.models import profiles
from app.modules.content.models import remote_config
from app.modules.placement.service import lock_user
from app.modules.plan import evidence, rules
from app.modules.plan.models import plans, streaks, tasks
from app.modules.plan.schemas import Assignment, NetRange, PlanTask, Today


async def calendar(db: AsyncSession) -> tuple[date, int]:
    config = dict(
        (
            await db.execute(
                select(remote_config).where(
                    remote_config.c.key.in_(("exam_date", "mock_day"))
                )
            )
        )
        .tuples()
        .all()
    )
    if not config.get("exam_date") or config.get("mock_day") not in rules.WEEKDAYS:
        raise ApiError(503, "service_unavailable", "Planning configuration missing")
    return date.fromisoformat(config["exam_date"]), rules.WEEKDAYS.index(config["mock_day"])


async def carry_forward(
    db: AsyncSession,
    history: list[RowMapping],
    day: date,
    exam: date,
    mock: int,
    inputs: evidence.Evidence,
) -> RowMapping | None:
    regular_end = exam - rules.DAY * rules.NEAR_EXAM
    deadlines: dict[str, date] = {}
    for topic in inputs.topics:
        for lesson_id, _ in topic.lessons:
            deadlines["lesson:" + lesson_id] = regular_end
        if topic.questions >= 10:
            deadlines["topic_test:" + topic.id] = exam if topic.opened else regular_end
    latest_done = {r["task_key"]: r["plan_date"] for r in history if r["state"] == "done"}
    missed = [
        r
        for r in history
        if r["included"]
        and r["state"] != "done"
        and r["plan_date"] < day
        and r["type"] in ("lesson", "topic_test")
        and day < deadlines.get(r["task_key"], date.min)
        and not r["carried_on"]
        and latest_done.get(r["task_key"], date.min) < r["plan_date"]
    ]
    by_key: dict[str, RowMapping] = {}
    for r in missed:
        by_key.setdefault(r["task_key"], r)
    fresh = [r for r in by_key.values() if not r["carry_on"]]
    due = [r for r in by_key.values() if r["carry_on"] and r["carry_on"] <= day]
    for row, when in zip(
        fresh,
        rules.distribute(day, mock, [deadlines[r["task_key"]] for r in fresh]),
        strict=True,
    ):
        await db.execute(update(tasks).where(tasks.c.id == row["id"]).values(carry_on=when))
        if when is not None and when <= day:
            due.append(row)
    return next(iter(due), None)


def still_available(scheduled: list[RowMapping], inputs: evidence.Evidence) -> bool:
    lessons = {id for t in inputs.topics for id, _ in t.lessons}
    counts = {t.id: t.questions for t in inputs.topics}
    for task in scheduled:
        if not task["included"] or task["state"] == "done":
            continue
        ref = Assignment.model_validate(task["ref"])
        if ref.kind == "lesson" and ref.content_id not in lessons:
            return False
        if ref.kind == "mock" and ref.content_id not in inputs.mock_ids:
            return False
        if ref.kind == "topic_test" and counts.get(ref.topic_id or "", 0) < ref.count:
            return False
    return True


async def build_plan(
    db: AsyncSession, user: UUID, now: datetime
) -> tuple[RowMapping, evidence.Evidence, date, int]:
    day = now.astimezone(ISTANBUL).date()
    prefs = (
        await db.execute(
            select(profiles.c.daily_minutes, profiles.c.score_type).where(
                profiles.c.user_id == user
            )
        )
    ).one_or_none()
    if not prefs:
        raise ApiError(409, "conflict", "Complete onboarding first")
    exam, mock = await calendar(db)
    history = await evidence.history(db, user)
    inputs = await evidence.read(db, user, day, now, history)
    plan = (
        (
            await db.execute(
                select(plans).where(plans.c.user_id == user, plans.c.plan_date == day)
            )
        )
        .mappings()
        .one_or_none()
    )
    scheduled = [r for r in history if r["plan_date"] == day]
    if (
        plan
        and not plan["needs_rebuild"]
        and plan["daily_minutes"] == prefs.daily_minutes
        and still_available(scheduled, inputs)
    ):
        return plan, inputs, exam, mock
    if plan is None:
        plan = (
            (
                await db.execute(
                    insert(plans)
                    .values(
                        id=uuid4(),
                        user_id=user,
                        plan_date=day,
                        daily_minutes=prefs.daily_minutes,
                    )
                    .returning(plans)
                )
            )
            .mappings()
            .one()
        )
    else:
        plan = (
            (
                await db.execute(
                    update(plans)
                    .where(plans.c.id == plan["id"])
                    .values(daily_minutes=prefs.daily_minutes, needs_rebuild=False)
                    .returning(plans)
                )
            )
            .mappings()
            .one()
        )
    kept = [Assignment.model_validate(r["ref"]) for r in scheduled if r["state"] == "done"]
    carry = await carry_forward(db, history, day, exam, mock, inputs)
    specs = rules.build(
        day=day,
        exam=exam,
        minutes=prefs.daily_minutes,
        score_type=prefs.score_type,
        mock_weekday=mock,
        due=inputs.due,
        topics=inputs.topics,
        mock=inputs.mock,
        kept=kept,
        closed=plan["completed_at"] is not None,
        carry=(carry["type"], carry["ref"]["content_id"]) if carry else None,
    )
    await db.execute(
        update(tasks).where(tasks.c.plan_id == plan["id"]).values(included=False)
    )
    rank = {"review": 0, "lesson": 1, "topic_test": 2, "mock": 0}
    for index, item in enumerate(sorted(specs, key=lambda a: rank[a.kind])):
        data = dict(
            ref=item.model_dump(),
            position=index,
            type=item.kind,
            est_quarters=item.quarters,
            included=True,
        )
        await db.execute(
            upsert(tasks)
            .values(
                id=uuid4(), plan_id=plan["id"], task_key=item.key, state="pending", **data
            )
            .on_conflict_do_update(index_elements=["plan_id", "task_key"], set_=data)
        )
        if carry and carry["task_key"] == item.key:
            await db.execute(
                update(tasks).where(tasks.c.id == carry["id"]).values(carried_on=day)
            )
    await credit(db, plan["id"], now)
    return plan, inputs, exam, mock


async def sync_streak(db: AsyncSession, user: UUID, day: date) -> tuple[rules.Streak, bool]:
    days = (
        await db.execute(
            select(plans.c.plan_date, plans.c.completed_at)
            .where(plans.c.user_id == user, plans.c.plan_date <= day)
            .order_by(plans.c.plan_date)
        )
    ).all()
    complete = any(r.plan_date == day and r.completed_at for r in days)
    stats = rules.streak(
        days[0].plan_date, day, (r.plan_date for r in days if r.completed_at)
    )
    values = dict(
        current=stats.current,
        longest=stats.longest,
        last_completed_on=stats.last_completed_on,
        freeze_used_week=stats.freeze_used_week,
    )
    await db.execute(
        upsert(streaks)
        .values(user_id=user, **values)
        .on_conflict_do_update(index_elements=["user_id"], set_=values)
    )
    return stats, complete


async def credit(db: AsyncSession, plan_id: UUID, now: datetime) -> None:
    c = tasks.c
    rows = (
        await db.execute(
            select(c.state, c.included, c.est_quarters).where(c.plan_id == plan_id)
        )
    ).all()
    active = [r for r in rows if r.included]
    spent = sum(r.est_quarters for r in rows if r.state == "done")
    budget = await db.scalar(select(plans.c.daily_minutes).where(plans.c.id == plan_id))
    if (active and all(r.state == "done" for r in active)) or (
        not active and budget and spent >= budget * 4
    ):
        owner = await db.scalar(
            update(plans)
            .where(plans.c.id == plan_id, plans.c.completed_at.is_(None))
            .values(completed_at=now)
            .returning(plans.c.user_id)
        )
        if owner:
            await sync_streak(db, owner, now.astimezone(ISTANBUL).date())


async def recompute_existing(db: AsyncSession, user: UUID, now: datetime) -> None:
    day = now.astimezone(ISTANBUL).date()
    if await db.scalar(
        select(plans.c.id).where(plans.c.user_id == user, plans.c.plan_date == day)
    ):
        await build_plan(db, user, now)


def display(r: RowMapping, next_id: UUID | None) -> PlanTask:
    a = Assignment.model_validate(r["ref"])
    return PlanTask(
        id=r["id"],
        kind=a.kind,
        content_id=a.content_id,
        title=a.title,
        subtest=a.subtest,
        count=a.count,
        minutes=a.quarters / 4,
        state=r["state"],
        is_next=r["id"] == next_id,
    )


async def today(db: AsyncSession, user: UUID, now: datetime) -> Today:
    await lock_user(db, user)
    plan, inputs, exam, mock = await build_plan(db, user, now)
    day = plan["plan_date"]
    rows = (
        (
            await db.execute(
                select(tasks)
                .where(tasks.c.plan_id == plan["id"])
                .order_by(tasks.c.position, tasks.c.id)
            )
        )
        .mappings()
        .all()
    )
    current = [r for r in rows if r["included"]]
    done = sum(r["state"] == "done" for r in current)
    next_id = next((r["id"] for r in current if r["state"] != "done"), None)
    stats, complete = await sync_streak(db, user, day)
    return Today(
        plan_date=day,
        days_to_exam=max(0, (exam - day).days),
        daily_minutes=plan["daily_minutes"],
        mock_day=day.weekday() == mock,
        tasks=[display(r, next_id) for r in current],
        earlier_completed=[
            display(r, None) for r in rows if not r["included"] and r["state"] == "done"
        ],
        total=len(current),
        done=done,
        day_completed=complete,
        percent=100
        if complete
        else rules.half_up(done * 100 / len(current))
        if current
        else 0,
        remaining_minutes=sum(r["est_quarters"] for r in current if r["state"] != "done")
        / 4,
        streak=stats.current,
        weekly_done=stats.weekly_done,
        weekly_goal=rules.WEEKLY_GOAL,
        net_range=NetRange(low=inputs.net_range[0], high=inputs.net_range[1])
        if inputs.net_range
        else None,
        net_change=inputs.net_change,
        priorities=inputs.priorities,
    )


async def task_action(
    db: AsyncSession, user: UUID, task_id: UUID, now: datetime, action: str | None
) -> PlanTask:
    if action:
        await lock_user(db, user)
    if action == "start":
        await recompute_existing(db, user, now)
    row = (
        (
            await db.execute(
                select(tasks, plans.c.plan_date)
                .join_from(tasks, plans)
                .where(tasks.c.id == task_id, plans.c.user_id == user)
            )
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        raise ApiError(404, "not_found", "Task not found")
    if not action or row["state"] == "done":
        return display(row, None)
    if not row["included"] or row["plan_date"] != now.astimezone(ISTANBUL).date():
        raise ApiError(409, "conflict", "Task is no longer current")
    if action == "complete" and row["state"] == "pending":
        raise ApiError(409, "conflict", "Start the task first")
    values = (
        dict(state="done", completed_at=now)
        if action == "complete"
        else dict(state="started")
    )
    saved = (
        (
            await db.execute(
                update(tasks).where(tasks.c.id == task_id).values(**values).returning(tasks)
            )
        )
        .mappings()
        .one()
    )
    if action == "complete":
        await credit(db, row["plan_id"], now)
    return display(saved, None)
