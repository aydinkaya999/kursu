import asyncio
import secrets
from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.schema import CreateSchema, DropSchema

from app.cli import import_documents
from app.core.settings import Settings
from app.modules.content.bundle import SAMPLE_FILE, Bundle, read_document
from app.modules.content.placeholders import make_placeholders


@pytest.fixture
def sample() -> Bundle:
    document: Bundle = read_document(SAMPLE_FILE)
    return document


@pytest.fixture
def catalogue_db(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Settings]:
    # Run the actual migration chain in a private namespace in the real PostgreSQL DB.
    url = make_url(Settings().database_url)
    schema = f"test_catalogue_{uuid4().hex}"
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(CreateSchema(schema))
    try:
        isolated = url.update_query_dict({"options": f"-csearch_path={schema}"})
        monkeypatch.setenv("DATABASE_URL", isolated.render_as_string(hide_password=False))
        monkeypatch.setenv("APP_ENV", "development")
        monkeypatch.setenv("PHOTO_STORAGE_DIR", str(tmp_path / "photos"))
        monkeypatch.setenv("JWT_SECRET", secrets.token_urlsafe(48))
        command.upgrade(
            Config(str(Path(__file__).resolve().parents[1] / "alembic.ini")), "head"
        )
        yield Settings()
    finally:
        with engine.begin() as connection:
            connection.execute(DropSchema(schema, cascade=True))
        engine.dispose()


@pytest.fixture
def engine(catalogue_db: Settings) -> Iterator[Engine]:
    engine = create_engine(catalogue_db.database_url)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def seeded(catalogue_db: Settings, sample: Bundle) -> Settings:
    config = read_document(SAMPLE_FILE.with_name("config.json"))
    asyncio.run(import_documents(catalogue_db, [config, sample]))
    return catalogue_db


@pytest.fixture
def demo(seeded: Settings, sample: Bundle) -> Settings:
    asyncio.run(import_documents(seeded, [make_placeholders(sample)]))
    return seeded
