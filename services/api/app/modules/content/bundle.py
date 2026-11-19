"""Read offline JSON documents and validate their versioned file contract."""

import json
from functools import cache
from pathlib import Path
from typing import Any, Never

from jsonschema import Draft202012Validator, FormatChecker

CONTENT_DIR = Path(__file__).resolve().parents[5] / "content"
SAMPLE_FILE = CONTENT_DIR / "seed/sample-content.json"
SCHEMA_FILE = CONTENT_DIR / "schema/bundle-v1.schema.json"
MARKER = "[ÖRNEK]"
type Row = dict[str, Any]
type Bundle = dict[str, Any]


class ContentError(ValueError):
    """An invalid bundle. Safe to report to the offline importer operator."""


def read_document(path: Path) -> Any:
    def reject_constant(value: str) -> Never:
        raise ContentError(f"Invalid JSON number {value}")

    with path.open(encoding="utf-8") as stream:
        try:
            return json.load(stream, parse_constant=reject_constant)
        except ValueError as error:
            raise ContentError(f"{path}: {error}") from error


@cache
def bundle_validator() -> Draft202012Validator:
    return Draft202012Validator(read_document(SCHEMA_FILE), format_checker=FormatChecker())


def validate_bundle(document: object, *, production: bool) -> Bundle:
    error = next(bundle_validator().iter_errors(document), None)
    if error:
        raise ContentError(f"{error.json_path}: {error.message}")
    assert isinstance(document, dict)
    for group, rows in document.items():
        if group in {"schema_version", "note"}:
            continue
        seen: set[str] = set()
        for row in rows:
            identifier = row["key" if group == "remote_config" else "id"]
            if identifier in seen:
                raise ContentError(f"{group}: duplicate ID {identifier!r}")
            seen.add(identifier)
            if production and row.get("is_placeholder"):
                raise ContentError(f"{identifier}: production refuses placeholders")
            if row.get("status") in ("published", "prerelease") and group in (
                "lessons",
                "questions",
            ):
                source = row["source"]
                if row.get("subtest_id") == "legislation" and source["kind"] != "law":
                    raise ContentError(f"{group}: {identifier} needs a law source")
                if source["kind"] == "law" and not source.get("quote"):
                    raise ContentError(
                        f"{group}: {identifier} needs the cited article text"
                    )
                if row.get("subtest_id") == "quantitative" and not row["solution_steps"]:
                    raise ContentError(f"{group}: {identifier} needs solution steps")
    for lesson in document.get("lessons", []):
        for check in lesson["check_questions"]:
            if check["card_position"] > len(lesson["cards"]):
                raise ContentError(f"{lesson['id']}: check refers to a missing card")
    return document
