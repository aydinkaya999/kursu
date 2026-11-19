import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import Engine, func, select
from study_support import practice_start

from app.cli import import_documents
from app.core.http import ISTANBUL, server_now
from app.core.settings import Settings
from app.main import create_app
from app.modules.content import models as bank
from app.modules.content.bundle import Bundle
from app.modules.content.placeholders import make_placeholders
from app.modules.placement.models import answers
from app.modules.practice.bank import select_items
from app.modules.practice.learning import (
    advance_mastery,
    difficulty,
    mastery_state,
    outcome,
)
from app.modules.practice.models import completions, mastery, reports, sessions

LAW = "lesson.legislation.firsat-ve-imkan-esitligi"
TOPIC = "quantitative.percent-ratio"


def guest(c: TestClient) -> dict[str, str]:
    tokens = c.post("/v1/auth/guest", json={"platform": "native"}).json()
    return {"Authorization": "Bearer " + tokens["access_token"]}


def post(
    c: TestClient, path: str, user: dict[str, str], data: dict[str, Any]
) -> dict[str, Any]:
    r = c.post(path, headers=user, json=data)
    r.raise_for_status()
    return dict(r.json())


def test_d2_d8_mastery_and_difficulty_mix() -> None:
    assert (
        outcome(True, True) == 0.5
        and outcome(False, True) == 0
        and outcome(True, False) == 1
    )
    assert advance_mastery(0, None) == 0.3 and advance_mastery(0.8, None) == 0.8
    assert advance_mastery(0.5, 0) == 0.4
    assert [
        mastery_state(v, n, done)
        for v, n, done in [(0, 0, False), (0.3, 0, True), (0.8, 7, True), (0.75, 8, True)]
    ] == ["not_started", "in_progress", "in_progress", "solid"]
    assert [difficulty(v) for v in (0.39, 0.4, 0.74, 0.75)] == [1, 2, 2, 3]
    bank_rows = [(f"{level}-{i}", level) for level in (1, 2, 3) for i in range(15)]
    for level in (1, 2, 3):
        ids = select_items(bank_rows, level, 15)
        assert len(set(ids)) == 15
        assert sum(x.startswith(str(level)) for x in ids) == 10
        assert all(abs(int(x[0]) - level) <= 1 for x in ids)


def test_les_why_checks_source_retry_completion_and_ownership(
    demo: Settings, engine: Engine
) -> None:
    app = create_app(demo)
    with TestClient(app) as c:
        auth, other = guest(c), guest(c)
        app.dependency_overrides[server_now] = lambda: datetime(
            2027, 2, 1, 12, tzinfo=ISTANBUL
        )
        library = c.get("/v1/study/lessons", headers=auth).json()
        assert any(
            lesson["id"] == LAW and not lesson["completed"]
            for group in library
            for t in group["topics"]
            for lesson in t["lessons"]
        )
        detail = c.get("/v1/lessons/" + LAW).json()
        assert (
            4 <= len(detail["cards"]) <= 6
            and detail["source"]["quote"]
            and len(detail["check_questions"]) == 2
        )
        state = practice_start(c, auth, "lesson_check", LAW)
        key = state["id"]
        url = "/v1/practice-sessions/" + key
        assert state == practice_start(c, auth, "lesson_check", LAW)
        assert c.get(url, headers=other).status_code == 404
        assert c.get("/v1/study/lessons").status_code == 401
        assert (
            c.post(
                "/v1/lessons/" + LAW + "/complete", headers=auth, json={"session_id": key}
            ).status_code
            == 409
        )
        first = state["question"]
        for pos in (1, 2):
            question = state["question"]
            assert (
                set(question) == {"id", "stem", "options"}
                and len(question["options"]) == 5
                and not state["feedback"]
            )
            with engine.connect() as db:
                item = (
                    db.execute(
                        select(bank.questions).where(bank.questions.c.id == question["id"])
                    )
                    .mappings()
                    .one()
                )
                card = db.scalar(
                    select(bank.lesson_check_questions.c.card_position).where(
                        bank.lesson_check_questions.c.lesson_id == LAW,
                        bank.lesson_check_questions.c.question_id == question["id"],
                    )
                )
            choice = (
                next(x for x in "ABCDE" if x != item["correct_option"])
                if pos == 1
                else item["correct_option"]
            )
            data = {
                "client_answer_id": str(uuid4()),
                "question_id": question["id"],
                "selected_option": choice,
                "not_sure": pos == 2,
            }

            def submit(_: int, payload: dict[str, Any] = data) -> dict[str, Any]:
                return post(c, url + "/answers", auth, payload)

            with ThreadPoolExecutor(max_workers=2) as pool:
                one, two = pool.map(submit, [0, 1])
            assert one == two == c.get(url, headers=auth).json()
            f = one["feedback"]
            assert f["rationales"][0] == {
                "option": choice,
                "text": item["rationales"][choice]["text"],
            }
            assert (
                len(f["rationales"]) == 5
                and f["source"]["quote"]
                and f["source"]["article"]
            )
            assert f["card_position"] == (card if pos == 1 else None)
            assert (
                c.post(
                    url + "/answers",
                    headers=auth,
                    json={**data, "not_sure": not data["not_sure"]},
                ).status_code
                == 409
            )
            state = post(c, url + "/advance", auth, {"question_id": question["id"]})
        assert state["state"] == "ready"
        result = post(c, "/v1/lessons/" + LAW + "/complete", auth, {"session_id": key})
        assert (
            result == post(c, url + "/finish", auth, {}) and result["state"] == "completed"
        )
        assert (
            post(c, url + "/advance", auth, {"question_id": first["id"]})["state"]
            == "completed"
        )
        with engine.connect() as db:
            assert db.scalar(select(func.count()).select_from(completions)) == 1
            row = db.execute(select(mastery)).one()
            assert row.value == 0.3 and row.answers_count == 2
        listed = c.get("/v1/study/lessons", headers=auth).json()
        assert any(
            lesson["completed"] and t["mastery"] == "in_progress"
            for g in listed
            for t in g["topics"]
            for lesson in t["lessons"]
            if lesson["id"] == LAW
        )


def test_test_why_steps_misconception_blank_and_adaptive_selection(
    demo: Settings, engine: Engine
) -> None:
    with TestClient(create_app(demo)) as c:
        who = guest(c)
        state = practice_start(c, who, "topic_test", TOPIC)
        key = state["id"]
        url = "/v1/practice-sessions/" + key
        assert state["total"] == 10
        with engine.connect() as db:
            ids = db.scalar(select(sessions.c.question_ids).where(sessions.c.id == key))
            assert ids is not None
            levels = dict(
                db.execute(
                    select(bank.questions.c.id, bank.questions.c.difficulty).where(
                        bank.questions.c.id.in_(ids)
                    )
                )
                .tuples()
                .all()
            )
            assert sum(levels[i] == 1 for i in ids) == 7
        for index in range(10):
            q = state["question"]
            id = q["id"]
            with engine.connect() as db:
                item = (
                    db.execute(select(bank.questions).where(bank.questions.c.id == id))
                    .mappings()
                    .one()
                )
            choice = next(
                (k for k, r in item["rationales"].items() if r.get("misconception_id")),
                item["correct_option"],
            )
            data = {
                "client_answer_id": str(uuid4()),
                "question_id": id,
                "selected_option": choice if index < 9 else None,
            }
            state = post(c, url + "/answers", who, data)
            if index < 9:
                f = state["feedback"]
                assert f["steps"] == item["solution_steps"] and f["steps"] and f["source"]
                if f["misconception_count"] >= 3:
                    assert f["suggest_lesson"] and f["related_lesson_id"]
                else:
                    assert not f["suggest_lesson"]
                if index == 5:
                    assert f["misconception_count"] >= 3
                state = post(c, url + "/advance", who, {"question_id": id})
            else:
                assert not state["feedback"] and state["state"] == "ready"
        assert post(c, url + "/finish", who, {})["state"] == "completed"
        with engine.connect() as db:
            assert db.scalar(select(func.count()).select_from(answers)) == 10


def test_cnt_3_concurrent_distinct_reports_withdraw_live_questions(
    demo: Settings, engine: Engine
) -> None:
    with TestClient(create_app(demo)) as c:
        users = [guest(c) for _ in range(4)]
        state = practice_start(c, users[0], "topic_test", TOPIC)
        url = "/v1/practice-sessions/" + state["id"]
        q = state["question"]["id"]
        data = {"question_id": q, "text": "İşlemi kontrol eder misiniz?"}
        assert post(c, "/v1/content-reports", users[0], data) == {"received": True}
        post(c, "/v1/content-reports", users[0], data)
        with engine.connect() as db:
            assert (
                db.scalar(select(bank.questions.c.status).where(bank.questions.c.id == q))
                != "quarantined"
            )
        with ThreadPoolExecutor(max_workers=2) as pool:
            assert all(
                pool.map(
                    lambda u: post(c, "/v1/content-reports", u, data)["received"],
                    users[1:3],
                )
            )
        with engine.connect() as db:
            assert (
                db.scalar(select(func.count()).select_from(reports)) == 3
                and db.scalar(
                    select(bank.questions.c.status).where(bank.questions.c.id == q)
                )
                == "quarantined"
            )
        assert (
            c.post(
                url + "/answers",
                headers=users[0],
                json={
                    "question_id": q,
                    "client_answer_id": str(uuid4()),
                    "selected_option": "A",
                },
            ).status_code
            == 409
        )
        current = c.get(url, headers=users[0]).json()
        assert current["question"]["id"] != q and not current["feedback"]
        assert (
            c.post(
                "/v1/content-reports", headers=users[3], json={**data, "text": "  "}
            ).status_code
            == 422
        )
        assert (
            c.post(
                "/v1/content-reports",
                headers=users[3],
                json={**data, "question_id": "missing"},
            ).status_code
            == 404
        )


def test_topic_test_uses_updated_mastery_for_next_session(
    demo: Settings, engine: Engine
) -> None:
    with TestClient(create_app(demo)) as c, engine.connect() as db:
        who = guest(c)
        first = practice_start(c, who, "topic_test", TOPIC)
        url = "/v1/practice-sessions/" + first["id"]
        before = db.scalar(
            select(sessions.c.question_ids).where(sessions.c.id == first["id"])
        )
        state = first
        for _ in range(first["total"]):
            question = state["question"]["id"]
            correct = db.scalar(
                select(bank.questions.c.correct_option).where(
                    bank.questions.c.id == question
                )
            )
            post(
                c,
                url + "/answers",
                who,
                {
                    "question_id": question,
                    "selected_option": correct,
                    "client_answer_id": str(uuid4()),
                },
            )
            state = post(c, url + "/advance", who, {"question_id": question})
        post(c, url + "/finish", who, {})
        catalogue = c.get("/v1/study/lessons", headers=who).json()
        assert (
            next(t["mastery"] for s in catalogue for t in s["topics"] if t["id"] == TOPIC)
            == "solid"
        )
        second = practice_start(c, who, "topic_test", TOPIC)
        after = db.scalar(
            select(sessions.c.question_ids).where(sessions.c.id == second["id"])
        )
        assert (
            before is not None and after is not None and not set(before).intersection(after)
        )
        levels = list(
            db.scalars(
                select(bank.questions.c.difficulty).where(bank.questions.c.id.in_(after))
            )
        )
        assert levels.count(3) == 7 and levels.count(2) == 3


def test_quarantine_withdraws_dependent_lessons_mocks_and_saved_feedback(
    demo: Settings, sample: Bundle, engine: Engine
) -> None:
    with TestClient(create_app(demo)) as c:
        users = [guest(c) for _ in range(3)]
        checks, slots = bank.lesson_check_questions.c, bank.mock_exam_questions.c
        with engine.connect() as db:
            lesson, question, mock = db.execute(
                select(checks.lesson_id, checks.question_id, slots.mock_exam_id)
                .join_from(
                    bank.lesson_check_questions,
                    bank.mock_exam_questions,
                    checks.question_id == slots.question_id,
                )
                .where(checks.position == 1)
                .limit(1)
            ).one()
        before = practice_start(c, users[0], "lesson_check", lesson)
        url = "/v1/practice-sessions/" + before["id"]
        assert before["question"]["id"] == question
        assert post(
            c,
            url + "/answers",
            users[0],
            {
                "question_id": question,
                "client_answer_id": str(uuid4()),
                "selected_option": "A",
            },
        )["feedback"]
        assert mock in {m["id"] for m in c.get("/v1/mocks").json()}
        for auth in users:
            post(
                c,
                "/v1/content-reports",
                auth,
                {"question_id": question, "text": "Kontrol edin."},
            )
        # Re-import the same offline bundles that originally published this question.
        asyncio.run(import_documents(demo, [sample, make_placeholders(sample)]))
        assert c.get(url, headers=users[0]).status_code == 409
        assert c.get("/v1/lessons/" + lesson).status_code == 404
        assert lesson not in {entry["id"] for entry in c.get("/v1/lessons").json()}
        assert mock not in {m["id"] for m in c.get("/v1/mocks").json()}
        assert lesson not in {
            entry["id"]
            for section in c.get("/v1/study/lessons", headers=users[1]).json()
            for topic in section["topics"]
            for entry in topic["lessons"]
        }
        # Moderation status outlives the reporters' personal data.
        with engine.begin() as db:
            db.execute(reports.delete())
        asyncio.run(import_documents(demo, [make_placeholders(sample)]))
        assert c.get("/v1/lessons/" + lesson).status_code == 404


def test_updated_lesson_starts_with_its_new_checks(demo: Settings, sample: Bundle) -> None:
    with TestClient(create_app(demo)) as c:
        who = guest(c)
        old = practice_start(c, who, "lesson_check", LAW)
        lesson = sample["lessons"][0]
        replacement = sample["questions"][0]["id"]
        lesson["check_questions"][0]["question_id"] = replacement
        asyncio.run(import_documents(demo, [{"schema_version": 1, "lessons": [lesson]}]))
        url = "/v1/practice-sessions/" + old["id"]
        assert c.get(url, headers=who).status_code == 409
        assert (
            c.post(
                url + "/answers",
                headers=who,
                json={
                    "question_id": old["question"]["id"],
                    "client_answer_id": str(uuid4()),
                    "selected_option": "B",
                },
            ).status_code
            == 409
        )
        fresh = practice_start(c, who, "lesson_check", LAW)
        assert fresh["id"] != old["id"] and fresh["question"]["id"] == replacement
