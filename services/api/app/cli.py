"""Offline content commands for operators and local setup."""

import argparse
import asyncio
import json
from collections.abc import Iterable
from pathlib import Path
from tempfile import TemporaryDirectory

from sqlalchemy.exc import DBAPIError

from app.core.db import Database
from app.core.http import server_now
from app.core.settings import Settings
from app.modules.content.bundle import (
    SAMPLE_FILE,
    ContentError,
    read_document,
    validate_bundle,
)
from app.modules.content.importer import import_bundle
from app.modules.content.placeholders import make_placeholders
from app.modules.mocks.service import submit_expired
from app.modules.photos.service import purge
from app.modules.photos.storage import PhotoStore


async def import_documents(settings: Settings, documents: Iterable[object]) -> None:
    database = Database(settings.database_url)
    try:
        async with database.sessions.begin() as session:
            for document in documents:
                await import_bundle(session, document, production=settings.production)
    finally:
        await database.engine.dispose()


async def expire(settings: Settings) -> int:
    database = Database(settings.database_url)
    try:
        async with database.sessions() as db:
            return await submit_expired(db, server_now())
    finally:
        await database.engine.dispose()


async def delete_expired_photos(settings: Settings) -> int:
    database = Database(settings.database_url)
    try:
        async with database.sessions() as db:
            return await purge(db, PhotoStore(settings.photo_storage_dir), server_now())
    finally:
        await database.engine.dispose()


def run(args: argparse.Namespace, settings: Settings) -> None:
    if args.command == "delete-expired-photos":
        print(f"Removed {asyncio.run(delete_expired_photos(settings))} private images.")
        return
    if args.command == "submit-expired-mocks":
        print(f"Submitted {asyncio.run(expire(settings))} expired attempts.")
        return
    if args.command == "make-placeholders":
        if settings.production:
            raise ContentError("production refuses placeholders")
        bundle = make_placeholders(read_document(SAMPLE_FILE))
        if args.output:
            validate_bundle(bundle, production=settings.production)
            with TemporaryDirectory(dir=args.output.parent) as directory:
                path = Path(directory) / "bundle.json"
                path.write_text(
                    json.dumps(bundle, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                path.replace(args.output)
            return
        documents: Iterable[object] = [bundle]
    else:
        documents = (read_document(path) for path in args.files)
    asyncio.run(import_documents(settings, documents))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("delete-expired-photos", help="remove expired photos and files")
    commands.add_parser("submit-expired-mocks", help="submit due timed mocks")
    importer = commands.add_parser(
        "import-content", help="validate and upsert offline JSON"
    )
    importer.add_argument("files", nargs="+", type=Path)
    generator = commands.add_parser(
        "make-placeholders", help="generate the development bank"
    )
    generator.add_argument("--output", type=Path, help="write a JSON bundle to this file")
    args = parser.parse_args()
    try:
        run(args, Settings())
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    except DBAPIError as error:
        parser.exit(1, f"Database rejected the import: {error.orig}\n")
    if args.command in {"import-content", "make-placeholders"}:
        print("Content ready.")


if __name__ == "__main__":
    main()
