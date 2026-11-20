"""Serve an isolated migrated and seeded PostgreSQL schema for UI tests."""

import argparse
import asyncio
import os
import secrets
import signal
from datetime import date, timedelta
from pathlib import Path
from types import FrameType
from uuid import uuid4

import uvicorn
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.schema import CreateSchema, DropSchema

from app.cli import import_documents
from app.core.http import ISTANBUL, ServerTime, Session, server_now
from app.core.settings import Settings
from app.modules.accounts.security import CurrentUser
from app.modules.content.bundle import SAMPLE_FILE, read_document
from app.modules.content.models import remote_config
from app.modules.content.placeholders import make_placeholders
from app.modules.notebook.models import entitlements
from app.modules.placement.schemas import Submission
from app.modules.placement.service import lock_user
from app.modules.practice import service as practice
from app.modules.practice.schemas import PracticeStart


def stop(signum: int, frame: FrameType | None) -> None:
    # Uvicorn re-raises SIGTERM after shutting down. Unwind the schema's finally block.
    raise SystemExit(0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8100)
    args = parser.parse_args()
    url = make_url(Settings().database_url)
    engine = create_engine(url)
    schema = "test_ui_" + uuid4().hex
    signal.signal(signal.SIGTERM, stop)
    with engine.begin() as conn:
        conn.execute(CreateSchema(schema))
    try:
        isolated = url.update_query_dict({"options": f"-csearch_path={schema}"})
        os.environ.update(
            DATABASE_URL=isolated.render_as_string(hide_password=False),
            APP_ENV="test",
            JWT_SECRET=secrets.token_urlsafe(48),
        )
        command.upgrade(
            Config(str(Path(__file__).resolve().parents[1] / "alembic.ini")), "head"
        )
        sample = read_document(SAMPLE_FILE)
        config = read_document(SAMPLE_FILE.with_name("config.json"))
        # Keep these UI journeys in a study season even when the example exam is past.
        day = server_now().astimezone(ISTANBUL).date()
        for item in config["remote_config"]:
            # Use a regular study day here. API tests cover mock Sundays.
            if item["key"] == "mock_day" and day.weekday() == 6:
                item["value"] = "saturday"
            if item["key"] == "exam_date" and date.fromisoformat(
                item["value"]
            ) <= day + timedelta(days=30):
                item["value"] = (day + timedelta(days=90)).isoformat()
            if item["key"] == "results_date" and date.fromisoformat(
                item["value"]
            ) <= day + timedelta(days=90):
                item["value"] = (day + timedelta(days=124)).isoformat()
        asyncio.run(
            import_documents(
                Settings(),
                [
                    config,
                    sample,
                    make_placeholders(sample),
                ],
            )
        )
        from app.main import create_app
        from app.modules.accounts.email_login import email_sender

        app = create_app()

        @app.post("/fixtures/season-pass")
        async def season_pass(db: Session, user: CurrentUser) -> None:
            """Grant a pass for the unlimited-plan browser journey."""
            await lock_user(db, user)
            until = await db.scalar(
                select(remote_config.c.value).where(remote_config.c.key == "results_date")
            )
            await db.execute(
                entitlements.insert().values(
                    user_id=user,
                    kind="season_pass",
                    source="web",
                    valid_until=date.fromisoformat(str(until)),
                )
            )
            await db.commit()

        @app.post("/fixtures/paid-review")
        async def paid_review(db: Session, user: CurrentUser, now: ServerTime) -> None:
            await season_pass(db, user)
            await lock_user(db, user)
            yesterday = now - timedelta(days=1)
            state = await practice.start(
                db,
                user,
                PracticeStart(
                    kind="lesson_check",
                    content_id="lesson.legislation.firsat-ve-imkan-esitligi",
                ),
                yesterday,
            )
            assert state.question
            await practice.answer(
                db,
                user,
                state.id,
                Submission(
                    question_id=state.question.id,
                    selected_option="B",
                    not_sure=False,
                    client_answer_id=uuid4(),
                ),
                yesterday,
            )
            await db.commit()

        mailbox = Path(__file__).resolve().parents[3] / "apps/app/test-results/mailbox"

        class TestInbox:
            def send(self, email: str, code: str) -> None:
                from hashlib import sha256

                mailbox.mkdir(parents=True, exist_ok=True)
                (mailbox / sha256(email.encode()).hexdigest()).write_text(code)

        app.dependency_overrides[email_sender] = TestInbox
        uvicorn.run(app, host="127.0.0.1", port=args.port)
    finally:
        with engine.begin() as conn:
            conn.execute(DropSchema(schema, cascade=True))
        engine.dispose()


if __name__ == "__main__":
    main()
