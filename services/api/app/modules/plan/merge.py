from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.plan.models import plans, tasks


async def merge_plans(db: AsyncSession, source: UUID, target: UUID) -> None:
    incoming = (
        (
            await db.execute(
                select(plans).where(plans.c.user_id == source).order_by(plans.c.plan_date)
            )
        )
        .mappings()
        .all()
    )
    for old in incoming:
        existing = (
            (
                await db.execute(
                    select(plans).where(
                        plans.c.user_id == target, plans.c.plan_date == old["plan_date"]
                    )
                )
            )
            .mappings()
            .one_or_none()
        )
        if not existing:
            await db.execute(
                update(plans).where(plans.c.id == old["id"]).values(user_id=target)
            )
            continue
        dest = existing["id"]
        known = {
            r["task_key"]: r
            for r in (
                await db.execute(select(tasks).where(tasks.c.plan_id == dest))
            ).mappings()
        }
        for t in (
            (await db.execute(select(tasks).where(tasks.c.plan_id == old["id"])))
            .mappings()
            .all()
        ):
            other = known.get(t["task_key"])
            if not other:
                await db.execute(
                    update(tasks)
                    .where(tasks.c.id == t["id"])
                    .values(plan_id=dest, included=False)
                )
            elif t["state"] == "done" or (
                t["state"] == "started" and other["state"] == "pending"
            ):
                changes = dict(state=t["state"], completed_at=t["completed_at"])
                if t["type"] == "review" and t["state"] == "done":
                    ref = dict(t["ref"])
                    if other["state"] == "done":
                        ref["objectives"] = sorted(
                            set(ref["objectives"]) | set(other["ref"]["objectives"])
                        )
                        ref["entry_keys"] = sorted(
                            set(ref.get("entry_keys", []))
                            | set(other["ref"].get("entry_keys", []))
                        )
                        ref["count"] = len(set(ref["objectives"]) | set(ref["entry_keys"]))
                        ref["quarters"] = ref["count"] * 5
                    changes.update(ref=ref, est_quarters=ref["quarters"])
                await db.execute(
                    update(tasks).where(tasks.c.id == other["id"]).values(**changes)
                )
        # Force the next read to reconcile the active schedule with both histories.
        await db.execute(
            update(plans)
            .where(plans.c.id == dest)
            .values(
                needs_rebuild=True,
                completed_at=existing["completed_at"] or old["completed_at"],
            )
        )
        await db.execute(delete(plans).where(plans.c.id == old["id"]))
