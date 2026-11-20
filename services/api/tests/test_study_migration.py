from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, func, select

from app.core.settings import Settings
from app.modules.accounts.models import users
from app.modules.content.bundle import Bundle
from app.modules.notebook.models import entries
from app.modules.placement.models import answers, attempts
from app.modules.plan.models import plans, tasks
from app.modules.practice.models import completions, mastery


def test_m6_replays_m3_answers_and_m5_lessons_in_order(
    seeded: Settings, sample: Bundle, engine: Engine
) -> None:
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    previous = "0005_daily_plan"
    command.downgrade(config, previous)
    user, placement, plan = uuid4(), uuid4(), uuid4()
    at = datetime(2027, 2, 1, 10, tzinfo=UTC)
    lesson = sample["lessons"][0]
    with engine.begin() as db:
        db.execute(users.insert().values(id=user, is_guest=True))
        db.execute(
            attempts.insert().values(
                id=placement,
                user_id=user,
                kind="full",
                state="active",
                position=3,
                levels={},
                started_at=at,
            )
        )
        db.execute(
            plans.insert().values(
                id=plan, user_id=user, plan_date=at.date(), daily_minutes=60
            )
        )
        db.execute(
            tasks.insert().values(
                id=uuid4(),
                plan_id=plan,
                task_key="lesson:" + lesson["id"],
                type="lesson",
                position=1,
                ref={"content_id": lesson["id"]},
                est_quarters=20,
                state="done",
                included=True,
                completed_at=at + timedelta(minutes=1),
            )
        )
        for pos, item in enumerate(sample["questions"][:2], 1):
            db.execute(
                answers.insert().values(
                    id=uuid4(),
                    client_answer_id=uuid4(),
                    user_id=user,
                    placement_id=placement,
                    position=pos,
                    subtest_id=item["subtest_id"],
                    topic_id=item["topic_id"],
                    question_id=item["id"],
                    selected_option="B",
                    not_sure=False,
                    is_correct=item["correct_option"] == "B",
                    answered_at=at + timedelta(minutes=(pos - 1) * 2),
                )
            )
    for run in range(2):
        command.upgrade(config, "head")
        with engine.connect() as db:
            result = db.execute(select(mastery)).one()
            assert result.value == pytest.approx(0.24) and result.answers_count == 2
            assert db.scalar(select(completions.c.lesson_id)) == lesson["id"]
            entry = db.execute(select(entries)).one()
            assert entry.first_question_id == sample["questions"][1]["id"]
            assert entry.correct_streak == 0 and entry.status == "open"
            assert entry.due_on == at.date() + timedelta(days=1)
            assert (
                db.scalar(select(answers.c.misconception_id).where(answers.c.position == 2))
                == sample["questions"][1]["rationales"]["B"]["misconception_id"]
            )
        if run == 0:
            command.downgrade(config, previous)
            with engine.connect() as db:
                assert db.scalar(select(func.count()).select_from(answers)) == 2
