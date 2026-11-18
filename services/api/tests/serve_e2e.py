"""Serve an isolated migrated and seeded PostgreSQL schema for UI tests."""

import argparse
import asyncio
import os
import secrets
import signal
from pathlib import Path
from types import FrameType
from uuid import uuid4

import uvicorn
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.schema import CreateSchema, DropSchema

from app.cli import import_documents
from app.core.settings import Settings
from app.modules.content.bundle import SAMPLE_FILE, read_document
from app.modules.content.placeholders import make_placeholders


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
        asyncio.run(
            import_documents(
                Settings(),
                [
                    read_document(SAMPLE_FILE.with_name("config.json")),
                    sample,
                    make_placeholders(sample),
                ],
            )
        )
        uvicorn.run("app.main:app", host="127.0.0.1", port=args.port)
    finally:
        with engine.begin() as conn:
            conn.execute(DropSchema(schema, cascade=True))
        engine.dispose()


if __name__ == "__main__":
    main()
