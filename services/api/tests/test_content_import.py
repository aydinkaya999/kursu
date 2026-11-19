import asyncio
import json
import os
import subprocess
import sys
from collections import Counter
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from sqlalchemy import Engine, func, literal_column, select, text
from sqlalchemy.exc import IntegrityError

from app.cli import import_documents
from app.core.settings import Settings
from app.modules.content import models as db
from app.modules.content.bundle import (
    MARKER,
    SAMPLE_FILE,
    SCHEMA_FILE,
    Bundle,
    ContentError,
    Row,
    read_document,
    validate_bundle,
)
from app.modules.content.placeholders import make_placeholders


def row_versions(engine: Engine) -> dict[str, list[str]]:
    with engine.connect() as conn:
        return {
            table.name: list(
                conn.scalars(
                    select(literal_column("xmin::text"))
                    .select_from(table)
                    .order_by(*table.primary_key)
                )
            )
            for table in db.metadata.sorted_tables
        }


def test_schema_validates_seed_and_rejects_malformed_bundles(sample: Bundle) -> None:
    Draft202012Validator.check_schema(read_document(SCHEMA_FILE))
    validate_bundle(sample, production=True)
    question = sample["questions"][0]
    alterations: list[Row] = [
        {"difficulty": 4},
        {"status": "live"},
        {"correct_option": "F"},
        {"source": {}},
        {
            "source": {
                "kind": "law",
                "short_name": question["source"]["short_name"],
                "article": 8,
            }
        },
        {"subtest_id": "quantitative", "solution_steps": []},
        {"options": {"A": "A"}},
        {"rationales": {**question["rationales"], "F": {}}},
        {"is_placeholder": True},
        {"stem": f"{MARKER} {question['stem']}"},
    ]
    for alteration in alterations:
        with pytest.raises(ContentError, match="questions"):
            validate_bundle(
                {"schema_version": 1, "questions": [{**question, **alteration}]},
                production=False,
            )
    for document in [
        {"schema_version": 2},
        {"schema_version": 1, "unknown": []},
        {"schema_version": 1, "questions": [question, question]},
    ]:
        with pytest.raises(ContentError):
            validate_bundle(document, production=False)


def test_les_1_and_les_2_lesson_card_and_check_requirements(sample: Bundle) -> None:
    lesson = sample["lessons"][0]
    alterations: list[Row] = [
        {"minutes": 2},
        {"minutes": 6},
        {"cards": lesson["cards"][:3]},
        {"cards": lesson["cards"] * 2},
        {"check_questions": lesson["check_questions"][:1]},
        {"check_questions": lesson["check_questions"] * 2},
    ]
    for alteration in alterations:
        with pytest.raises(ContentError, match="lessons"):
            validate_bundle(
                {"schema_version": 1, "lessons": [{**lesson, **alteration}]},
                production=False,
            )
    lesson["check_questions"][0]["card_position"] = 5
    with pytest.raises(ContentError, match="missing card"):
        validate_bundle(sample, production=False)


def test_cnt_6_sources_are_searchable_and_feedback_survives_import(
    seeded: Settings, sample: Bundle, engine: Engine
) -> None:
    law = {"kind": "law", "short_name": "1739 sayılı Kanun"}
    with engine.connect() as conn:
        q, lesson = db.questions.c, db.lessons.c
        affected = conn.scalars(
            select(q.id).where(q.source.contains({**law, "article": 8}))
        )
        assert set(affected) == {"q.legislation.0001", "q.legislation.0003"}
        assert (
            conn.execute(
                select(lesson.id).where(lesson.source.contains({**law, "articles": [8]}))
            ).scalar_one()
            == sample["lessons"][0]["id"]
        )
        stored = {row["id"]: row for row in conn.execute(select(db.questions)).mappings()}
        for question in sample["questions"]:
            assert all(
                stored[question["id"]][key] == value for key, value in question.items()
            )
        config = dict(conn.execute(select(db.remote_config)).tuples().all())
        assert config["exam_date"] == "2027-05-08"
        assert config["results_date"] == "2027-06-11"


def test_mock_1_demo_bank_covers_the_exam_distribution_placement_and_topic_tests(
    demo: Settings, engine: Engine, sample: Bundle
) -> None:
    with engine.connect() as conn:
        topics = conn.execute(select(db.topics)).mappings().all()
        assert len(topics) == 31
        assert sum(t["is_placeholder"] for t in topics) == 25
        questions = conn.execute(select(db.questions)).mappings().all()
        subjects = {q["id"]: q["subtest_id"] for q in questions}
        by_topic_level = Counter((q["topic_id"], q["difficulty"]) for q in questions)
        siblings = Counter(q["objective_id"] for q in questions)
        assert min(siblings.values()) >= 2
        for topic in topics:
            for level in (1, 2, 3):
                assert by_topic_level[topic["id"], level] >= 10
        assert {q["id"] for q in questions if not q["is_placeholder"]} == {
            q["id"] for q in sample["questions"]
        }
        for question in questions:
            assert question["stem"].startswith(MARKER) == question["is_placeholder"]

        for table in (db.lessons, db.mock_exams):
            for row in conn.execute(select(table)).mappings():
                assert row["title"].startswith(MARKER) == row["is_placeholder"]
        checks = conn.execute(
            select(db.lesson_check_questions.c.lesson_id, func.count()).group_by(
                db.lesson_check_questions.c.lesson_id
            )
        )
        assert all(count == 2 for _, count in checks)
        expected = [s["id"] for s in sample["subtests"] for _ in range(s["question_count"])]
        mock_ids = conn.scalars(select(db.mock_exams.c.id)).all()
        assert len(mock_ids) == 10
        slots = db.mock_exam_questions.c
        used: set[str] = set()
        for mock_id in mock_ids:
            ids = conn.scalars(
                select(slots.question_id)
                .where(slots.mock_exam_id == mock_id)
                .order_by(slots.position)
            ).all()
            assert len(ids) == len(set(ids)) == 80
            assert used.isdisjoint(ids)
            used.update(ids)
            assert [subjects[q] for q in ids] == expected


def test_identical_and_concurrent_imports_keep_row_versions(
    demo: Settings, sample: Bundle, engine: Engine
) -> None:
    first = row_versions(engine)
    config = read_document(SAMPLE_FILE.with_name("config.json"))
    generated = make_placeholders(sample)
    asyncio.run(import_documents(demo, [config, sample, generated]))

    async def repeat() -> None:
        await asyncio.gather(
            import_documents(demo, [sample]), import_documents(demo, [sample])
        )

    asyncio.run(repeat())
    assert row_versions(engine) == first


def test_upserts_reconcile_ordered_children_and_preserve_answered_questions(
    seeded: Settings, sample: Bundle, engine: Engine
) -> None:
    lesson = deepcopy(sample["lessons"][0])
    with engine.begin() as conn:
        # Emulate an existing study reference without implementing an answers table in M2.
        conn.execute(
            text("CREATE TABLE answered (question_id text REFERENCES questions(id))")
        )
        conn.execute(
            text("INSERT INTO answered VALUES (:q)"), {"q": sample["questions"][0]["id"]}
        )
    lesson["cards"].append(lesson["cards"][0].copy())
    lesson["check_questions"][0]["card_position"] = 5
    asyncio.run(import_documents(seeded, [{"schema_version": 1, "lessons": [lesson]}]))
    lesson["title"] = lesson["cards"][0]["title"]
    lesson["cards"].pop()
    lesson["check_questions"][0]["card_position"] = 2
    lesson["check_questions"].reverse()
    asyncio.run(import_documents(seeded, [{"schema_version": 1, "lessons": [lesson]}]))
    with engine.connect() as conn:
        assert conn.execute(select(db.lessons.c.title)).scalar_one() == lesson["title"]
        assert conn.scalar(select(func.count()).select_from(db.lesson_cards)) == 4
        checks = db.lesson_check_questions.c
        assert conn.execute(
            select(checks.question_id, checks.card_position).order_by(checks.position)
        ).tuples().all() == [
            (c["question_id"], c["card_position"]) for c in lesson["check_questions"]
        ]
        assert (
            conn.scalar(
                text(
                    "SELECT count(*) FROM answered JOIN questions "
                    "ON questions.id = answered.question_id"
                )
            )
            == 1
        )
        assert conn.scalar(select(func.count()).select_from(db.questions)) == len(
            sample["questions"]
        )


def test_invalid_references_and_wrong_mock_order_roll_back(
    demo: Settings, sample: Bundle, engine: Engine
) -> None:
    versions = row_versions(engine)
    sample["fields"][0]["name"] = sample["fields"][1]["name"]
    question = deepcopy(sample["questions"][0])
    question["rationales"]["A"]["misconception_id"] = "missing"
    with pytest.raises(ContentError, match="missing"):
        asyncio.run(
            import_documents(demo, [sample, {"schema_version": 1, "questions": [question]}])
        )
    question = {**sample["questions"][0], "objective_id": sample["objectives"][1]["id"]}
    with pytest.raises(IntegrityError):
        asyncio.run(
            import_documents(demo, [{"schema_version": 1, "questions": [question]}])
        )
    mock = make_placeholders(sample)["mock_exams"][0]
    mock["question_ids"].reverse()
    with pytest.raises(ContentError, match="distribution"):
        asyncio.run(
            import_documents(demo, [sample, {"schema_version": 1, "mock_exams": [mock]}])
        )
    assert row_versions(engine) == versions


def test_production_cli_rejects_whole_import_and_generator(
    catalogue_db: Settings, sample: Bundle, engine: Engine, tmp_path: Path
) -> None:
    def cli(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "app.cli", *args],
            cwd=Path(__file__).resolve().parents[1],
            env={
                **os.environ,
                "APP_ENV": "production",
                "DATABASE_URL": catalogue_db.database_url,
            },
            text=True,
            capture_output=True,
            check=False,
        )

    generated = make_placeholders(sample)
    fixture = tmp_path / "mixed.json"
    for group in (
        "topics",
        "objectives",
        "misconceptions",
        "questions",
        "lessons",
        "mock_exams",
    ):
        row = generated[group][0]
        with pytest.raises(ContentError, match="production refuses placeholders"):
            validate_bundle({"schema_version": 1, group: [row]}, production=True)
        with pytest.raises(ContentError, match=group):
            validate_bundle(
                {"schema_version": 1, group: [{**row, "is_placeholder": False}]},
                production=True,
            )
    fixture.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "questions": [sample["questions"][0], generated["questions"][0]],
            }
        ),
        encoding="utf-8",
    )
    response = cli("import-content", str(SAMPLE_FILE), str(fixture))
    assert response.returncode != 0
    assert "production refuses placeholders" in response.stderr
    assert all(not rows for rows in row_versions(engine).values())
    response = cli("make-placeholders")
    assert response.returncode != 0
    assert "production refuses placeholders" in response.stderr
    assert cli("import-content", str(SAMPLE_FILE)).returncode == 0
    assert len(row_versions(engine)["questions"]) == len(sample["questions"])
