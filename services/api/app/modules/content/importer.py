"""Upsert a validated offline bundle inside the caller's transaction."""

from datetime import datetime
from itertools import batched, groupby
from operator import itemgetter
from typing import Any

from sqlalchemy import ColumnElement, Table, case, delete, or_, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.content import models as db
from app.modules.content.bundle import ContentError, Row, validate_bundle


async def upsert(session: AsyncSession, table: Table, records: list[Row]) -> None:
    keys = [c.name for c in table.primary_key]
    # Project nested input onto the table; every row in a batch has the same columns.
    rows = [
        {
            c.name: record.get(c.name, False if c.name == "is_placeholder" else None)
            for c in table.columns
        }
        for record in records
    ]
    for batch in batched(rows, 200):
        statement = insert(table).values(list(batch))
        values: dict[str, ColumnElement[Any]] = {
            c.name: statement.excluded[c.name] for c in table.columns if c.name not in keys
        }
        if table is db.questions:
            # An offline publication bundle may predate a live quarantine.
            values["status"] = case(
                (
                    (table.c.status == "quarantined")
                    & statement.excluded.status.in_(("published", "prerelease")),
                    table.c.status,
                ),
                else_=statement.excluded.status,
            )
        changed = or_(*(table.c[k].is_distinct_from(v) for k, v in values.items()))
        await session.execute(
            statement.on_conflict_do_update(index_elements=keys, set_=values, where=changed)
        )


async def import_lessons(session: AsyncSession, lessons: list[Row]) -> None:
    cards, checks = [], []
    for lesson in lessons:
        key = lesson["id"]
        for position, card in enumerate(lesson["cards"], 1):
            cards.append(dict(card, lesson_id=key, position=position))
        for position, check in enumerate(lesson["check_questions"], 1):
            checks.append(dict(check, lesson_id=key, position=position))
        # Only a supplied lesson's card list is authoritative. Keep all other lessons.
        await session.execute(
            delete(db.lesson_cards).where(
                db.lesson_cards.c.lesson_id == key,
                db.lesson_cards.c.position > len(lesson["cards"]),
            )
        )
    await upsert(session, db.lesson_cards, cards)
    await upsert(session, db.lesson_check_questions, checks)


async def validate_misconceptions(session: AsyncSession, questions: list[Row]) -> None:
    referenced = {
        r["misconception_id"]
        for q in questions
        for r in q["rationales"].values()
        if "misconception_id" in r
    }
    if referenced:
        known = await session.scalars(
            select(db.misconceptions.c.id).where(db.misconceptions.c.id.in_(referenced))
        )
        missing = referenced.difference(known)
        if missing:
            raise ContentError(f"Unknown misconception IDs: {', '.join(sorted(missing))}")


async def validate_mock_distribution(session: AsyncSession) -> None:
    # A question or subtest edit can also invalidate a previously imported mock.
    sections = await session.execute(
        select(db.subtests.c.id, db.subtests.c.question_count).order_by(
            db.subtests.c.exam_order
        )
    )
    order = [subtest for subtest, count in sections for _ in range(count)]
    slots = db.mock_exam_questions
    items = await session.execute(
        select(slots.c.mock_exam_id, db.questions.c.subtest_id)
        .join_from(slots, db.questions)
        .order_by(slots.c.mock_exam_id, slots.c.position)
    )
    for mock_id, rows in groupby(items, key=itemgetter(0)):
        if [row.subtest_id for row in rows] != order:
            raise ContentError(
                f"{mock_id}: questions must follow the AGS exam distribution"
            )


async def import_bundle(
    session: AsyncSession, document: object, *, production: bool
) -> None:
    bundle = validate_bundle(document, production=production)
    # Serialize concurrent writers, including their child reconciliation and validation.
    await session.execute(text("SELECT pg_advisory_xact_lock(hashtext('kursu.content'))"))
    for table in (
        db.fields,
        db.subtests,
        db.remote_config,
        db.topics,
        db.objectives,
        db.misconceptions,
        db.lessons,
        db.questions,
    ):
        await upsert(session, table, bundle.get(table.name, []))

    questions = bundle.get("questions", [])
    await validate_misconceptions(session, questions)
    await import_lessons(session, bundle.get("lessons", []))
    mocks = bundle.get("mock_exams", [])
    headers, slots = [], []
    for mock in mocks:
        published_at = mock.get("published_at")
        timestamp = datetime.fromisoformat(published_at) if published_at else None
        if timestamp is not None and timestamp.utcoffset() is None:
            raise ContentError(f"{mock['id']}: published_at must include a timezone")
        headers.append(dict(mock, published_at=timestamp))
        for position, question_id in enumerate(mock["question_ids"], 1):
            slots.append(
                dict(mock_exam_id=mock["id"], position=position, question_id=question_id)
            )
    await upsert(session, db.mock_exams, headers)
    await upsert(session, db.mock_exam_questions, slots)
    if mocks or questions or bundle.get("subtests"):
        await validate_mock_distribution(session)
