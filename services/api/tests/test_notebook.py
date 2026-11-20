from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, select, update
from study_support import grant_pass, practice_start

from app.core.http import ISTANBUL, server_now
from app.core.settings import Settings
from app.main import create_app
from app.modules.content.models import questions, remote_config
from app.modules.notebook.models import entries
from app.modules.notebook.reviews import sibling
from app.modules.notebook.rules import Calendar, Schedule, entry_key, qualifies, transition
from app.modules.notebook.service import Item, groups, summary
from app.modules.placement.models import answers

EXAM = date(2027, 5, 8)
CALENDAR = Calendar(EXAM, (1, 3, 7, 14, 30))
DAY = timedelta(days=1)
MON = date(2027, 2, 1)
LAW = "lesson.legislation.firsat-ve-imkan-esitligi"
PRACTICE = "/v1/practice-sessions"
NOTEBOOK = "/v1/notebook"
SUMMARY = NOTEBOOK + "/summary"


@pytest.mark.parametrize(
    ("correct", "unsure", "capture"),
    [
        (True, False, False),
        (True, True, True),
        (False, True, True),
        (False, False, True),
        (None, False, False),
        (None, True, True),
    ],
)
def test_nb1_capture(correct: bool | None, unsure: bool, capture: bool) -> None:
    assert qualifies(correct, unsure) == capture
    assert entry_key("o", None) != entry_key("o", "m")


def test_nb2_groups_count_and_report_the_earliest_open_entry() -> None:
    def item(key: str, topic: str, misconception: str | None, due: date | None) -> Item:
        return Item(
            key, "o", "q", uuid4(), topic, topic, misconception, misconception, topic, due
        )

    items = [
        item("a", "t1", "m1", MON + DAY * 3),
        item("b", "t1", "m1", None),
        item("c", "t1", None, MON + DAY),
        item("d", "t2", None, MON - DAY),
    ]
    topic, other = groups(items, MON, "topic")
    assert (topic.id, topic.open_count, topic.learned_count, topic.next_due_on) == (
        "t1",
        2,
        1,
        MON + DAY,
    )
    assert other.next_due_days == 0
    unclassified, named = groups(items, MON, "misconception")
    assert (unclassified.name, unclassified.subtests, unclassified.open_count) == (
        None,
        ["t1", "t2"],
        2,
    )
    assert named.learned_count == 1 and named.next_due_days == 3
    counts = summary(items, MON, CALENDAR)
    assert (
        counts.open_count,
        counts.learned_count,
        counts.due_today,
        counts.due_tomorrow,
    ) == (3, 1, 1, 1)


def test_nb3_excludes_the_origin_and_reserved_slots() -> None:
    assert sibling(["origin", "a", "b"], "origin", ["a"]) == "b"
    assert sibling(["origin"], "origin") is None


def test_nb4_nb5_progression_resets_reopening_and_repeated_mistakes() -> None:
    def event(
        state: Schedule | None, day: date, correct: bool, review: bool = True
    ) -> Schedule:
        return transition(CALENDAR, day, state, correct=correct, review=review)

    first = event(None, MON, False, False)
    assert first.due_on == MON + DAY
    assert event(first, MON + DAY * 3, False, False).due_on == first.due_on
    second = event(first, MON + DAY, True)
    third = event(second, MON + DAY * 4, True)
    assert second.due_on == MON + DAY * 4 and third.due_on == MON + DAY * 11
    assert transition(CALENDAR, MON + DAY * 4, second, review=True, correct=None) == second
    reset = event(third, MON + DAY * 11, False)
    assert (reset.correct_streak, reset.interval_index, reset.due_on) == (
        0,
        0,
        MON + DAY * 12,
    )
    learned = event(third, MON + DAY * 11, True)
    assert learned.correct_streak == 3 and learned.due_on is None
    assert event(learned, MON + DAY * 20, False, False).correct_streak == 0
    assert [CALENDAR.due(MON, i, MON) for i in range(6)] == [
        MON + DAY * n for n in (1, 3, 7, 14, 30, 30)
    ]


def test_nb6_final_fortnight_uses_short_intervals_and_pulls_existing_work_forward() -> None:
    regular, near = EXAM - DAY * 14, EXAM - DAY * 13
    assert CALENDAR.intervals(regular) == (1, 3, 7, 14, 30)
    assert [CALENDAR.due(near, i, near) for i in range(5)] == [
        near + DAY * n for n in (1, 2, 3, 5, 5)
    ]
    work = Schedule(regular, 2, 2, regular + DAY * 7)
    assert work.effective_due(CALENDAR, near) == regular + DAY * 3
    for i in range(5):
        assert CALENDAR.due(EXAM - DAY, i, EXAM - DAY) == EXAM - DAY


def guest(c: TestClient) -> dict[str, str]:
    tokens = c.post("/v1/auth/guest", json={"platform": "native"}).json()
    return {"Authorization": "Bearer " + tokens["access_token"]}


def submit(
    c: TestClient,
    auth: dict[str, str],
    session: dict[str, Any],
    option: str | None,
    unsure: bool = False,
) -> dict[str, Any]:
    body = {
        "question_id": session["question"]["id"],
        "client_answer_id": str(uuid4()),
        "selected_option": option,
        "not_sure": unsure,
    }
    url = PRACTICE + "/" + session["id"] + "/answers"
    response = c.post(url, headers=auth, json=body)
    response.raise_for_status()
    assert c.post(url, headers=auth, json=body).json() == response.json()
    return dict(response.json())


def start_review(c: TestClient, auth: dict[str, str], **scope: str) -> dict[str, Any]:
    response = c.post(PRACTICE, headers=auth, json={"kind": "review", **scope})
    response.raise_for_status()
    return dict(response.json())


def finish(c: TestClient, auth: dict[str, str], feedback: dict[str, Any]) -> None:
    url = PRACTICE + "/" + feedback["id"]
    if feedback["state"] == "feedback":
        response = c.post(
            url + "/advance",
            headers=auth,
            json={"question_id": feedback["feedback"]["question"]["id"]},
        )
        assert response.json()["state"] == "ready"
    assert c.post(url + "/finish", headers=auth).json()["state"] == "completed"


def test_nb1_to_nb5_real_answers_expiry_resume_and_learned_groups(
    seeded: Settings, engine: Engine
) -> None:
    app = create_app(seeded)
    with TestClient(app) as c:
        auth, other = guest(c), guest(c)
        now = datetime(2027, 2, 1, 20, 59, tzinfo=UTC)
        app.dependency_overrides[server_now] = lambda: now
        assert c.get(NOTEBOOK).status_code == c.get(SUMMARY).status_code == 401
        assert c.get(NOTEBOOK, headers=auth).json() == []
        state = practice_start(c, auth, "lesson_check", LAW)
        original = state["question"]["id"]
        saved = submit(c, auth, state, "B")
        assert saved["feedback"]["notebook_due_days"] == 1
        assert c.get(SUMMARY, headers=auth).json()["due_tomorrow"] == 1
        assert c.get(SUMMARY, headers=other).json()["open_count"] == 0
        group = c.get(NOTEBOOK, headers=auth, params={"group_by": "misconception"}).json()[
            0
        ]
        assert group["name"] and group["id"] != state["topic_id"]
        assert c.get(NOTEBOOK, headers=auth).json()[0]["id"] == state["topic_id"]
        denied = c.post(PRACTICE, headers=auth, json={"kind": "review", "mode": "early"})
        assert denied.status_code == 403 and denied.json()["code"] == "entitlement_required"
        grant_pass(c, auth, engine, MON + DAY * 9)
        assert c.post(PRACTICE, headers=auth, json={"kind": "review"}).status_code == 409
        now += timedelta(minutes=1)
        assert c.get(SUMMARY, headers=auth).json()["due_today"] == 1
        assert (
            c.get(PRACTICE + "/" + state["id"], headers=auth).json()["feedback"][
                "notebook_due_days"
            ]
            == 0
        )
        assert (
            c.post(
                PRACTICE,
                headers=auth,
                json={"kind": "review", "group_by": "topic", "group_id": "unrelated"},
            ).status_code
            == 409
        )
        seen = set()
        for index in range(3):

            def open_review(_: int) -> dict[str, Any]:
                return start_review(
                    c, auth, mode="early", group_by="misconception", group_id=group["id"]
                )

            with ThreadPoolExecutor(2) as pool:
                review, resumed = pool.map(open_review, (0, 1))
            assert review == resumed and review["kind"] == "review"
            assert review["feedback"] is None and set(review["question"]) == {
                "id",
                "stem",
                "options",
            }
            question = review["question"]["id"]
            assert question != original
            if index < 2:
                assert question not in seen
            seen.add(question)
            with engine.connect() as db:
                selected, objective = db.execute(
                    select(questions.c.correct_option, questions.c.objective_id).where(
                        questions.c.id == question
                    )
                ).one()
                assert objective == db.scalar(select(entries.c.objective_id))
            saved = submit(c, auth, review, selected, unsure=index == 0)
            assert saved["feedback"]["is_correct"]
            finish(c, auth, saved)
            view = c.get(NOTEBOOK, headers=auth).json()[0]
            assert view["next_due_days"] == [3, 7, None][index]
            assert view["learned_count"] == int(index == 2)
        assert c.get(SUMMARY, headers=auth).json()["open_count"] == 0
        with engine.connect() as db:
            entry = db.execute(select(entries)).one()
            assert entry.correct_streak == 3 and entry.first_question_id == original
        now += DAY * 10
        url = PRACTICE + "/" + review["id"]
        for method, path, body in [
            ("GET", "", None),
            ("POST", "/finish", None),
            ("POST", "/advance", {"question_id": question}),
            (
                "POST",
                "/answers",
                {
                    "client_answer_id": str(uuid4()),
                    "question_id": question,
                    "selected_option": "A",
                },
            ),
        ]:
            assert c.request(method, url + path, headers=auth, json=body).status_code == 403
        assert c.get(url, headers=other).status_code == 404
        assert c.get(SUMMARY, headers=auth).json()["learned_count"] == 1


def test_review_replaces_with_same_objective_and_keeps_unavailable_or_blank_entries(
    seeded: Settings, engine: Engine
) -> None:
    app = create_app(seeded)
    with TestClient(app) as c:
        auth = guest(c)
        app.dependency_overrides[server_now] = lambda: datetime(
            2027, 2, 1, 13, tzinfo=ISTANBUL
        )
        grant_pass(c, auth, engine, EXAM)
        main = practice_start(c, auth, "lesson_check", LAW)
        original = main["question"]["id"]
        submit(c, auth, main, None, True)
        assert (
            c.get(NOTEBOOK, headers=auth, params={"group_by": "misconception"}).json()[0][
                "name"
            ]
            is None
        )
        review = start_review(c, auth, mode="early")
        first = review["question"]["id"]
        url = PRACTICE + "/" + review["id"]
        with engine.begin() as db:
            db.execute(
                update(questions)
                .where(questions.c.id == first)
                .values(status="quarantined")
            )
        replaced = c.get(url, headers=auth).json()
        assert replaced["question"]["id"] not in (first, original)
        with engine.connect() as db:
            assert db.scalar(
                select(questions.c.objective_id).where(
                    questions.c.id == replaced["question"]["id"]
                )
            ) == db.scalar(select(entries.c.objective_id))
            version = db.scalar(select(entries.c.last_answer_id))
        finish(c, auth, submit(c, auth, replaced, None))
        with engine.connect() as db:
            assert db.scalar(select(entries.c.last_answer_id)) == version
        active = start_review(c, auth, mode="early")
        with engine.begin() as db:
            db.execute(
                update(questions)
                .where(questions.c.id == active["question"]["id"])
                .values(status="retired")
            )
        assert c.get(PRACTICE + "/" + active["id"], headers=auth).json()["state"] == "ready"
        assert (
            c.post(PRACTICE + "/" + active["id"] + "/finish", headers=auth).status_code
            == 200
        )
        assert (
            c.post(
                PRACTICE, headers=auth, json={"kind": "review", "mode": "early"}
            ).status_code
            == 409
        )
        assert c.get(SUMMARY, headers=auth).json()["open_count"] == 1


def test_nb6_existing_schedule_and_remote_exam_change_reach_api(
    seeded: Settings, engine: Engine
) -> None:
    app = create_app(seeded)
    with TestClient(app) as c:
        auth = guest(c)
        app.dependency_overrides[server_now] = lambda: datetime.combine(
            MON, datetime.min.time(), ISTANBUL
        )
        grant_pass(c, auth, engine, EXAM)
        submit(c, auth, practice_start(c, auth, "lesson_check", LAW), "A", True)
        review = start_review(c, auth, mode="early")
        with engine.connect() as db:
            option = db.scalar(
                select(questions.c.correct_option).where(
                    questions.c.id == review["question"]["id"]
                )
            )
        finish(c, auth, submit(c, auth, review, option))
        with engine.begin() as db:
            db.execute(
                update(remote_config)
                .where(remote_config.c.key == "exam_date")
                .values(value=(MON + DAY).isoformat())
            )
        assert c.get(SUMMARY, headers=auth).json()["intervals"] == [1, 2, 3, 5]
        assert c.get(SUMMARY, headers=auth).json()["due_today"] == 1
        assert c.get(NOTEBOOK, headers=auth).json()[0]["next_due_on"] == MON.isoformat()
        retry = start_review(c, auth)
        with engine.connect() as db:
            answer = db.scalar(
                select(questions.c.correct_option).where(
                    questions.c.id == retry["question"]["id"]
                )
            )
        finish(c, auth, submit(c, auth, retry, "B" if answer == "A" else "A"))
        with engine.connect() as db:
            entry = db.execute(select(entries)).one()
            assert entry.correct_streak == entry.interval_index == 0 and entry.due_on == MON
            assert len(db.execute(select(answers)).all()) == 3


def test_overlapping_review_scopes_only_grade_once_and_partial_plan_requires_both_answers(
    seeded: Settings, engine: Engine
) -> None:
    app = create_app(seeded)
    with TestClient(app) as c:
        auth = guest(c)
        c.patch(
            "/v1/me/profile",
            headers=auth,
            json={
                "field_id": "sinif-ogretmenligi",
                "daily_minutes": 60,
                "attempt_kind": "first",
            },
        ).raise_for_status()
        now = datetime(2027, 2, 1, 12, tzinfo=ISTANBUL)
        app.dependency_overrides[server_now] = lambda: now
        grant_pass(c, auth, engine, EXAM)
        lesson = practice_start(c, auth, "lesson_check", LAW)
        first = submit(c, auth, lesson, "B")
        second = c.post(
            PRACTICE + "/" + lesson["id"] + "/advance",
            headers=auth,
            json={"question_id": first["feedback"]["question"]["id"]},
        ).json()
        submit(c, auth, second, "C", True)
        assert c.get(SUMMARY, headers=auth).json()["open_count"] == 2
        invalid = c.post(
            PRACTICE, headers=auth, json={"kind": "review", "group_by": "topic"}
        )
        assert invalid.status_code == 422
        group = start_review(c, auth, mode="early", group_by="misconception", group_id="")
        now += DAY
        task = c.get("/v1/plan/today", headers=auth).json()["tasks"][0]
        assert task["kind"] == "review" and task["count"] == 2
        planned = start_review(c, auth, task_id=task["id"])
        assert planned["id"] != group["id"] and planned["total"] == 2
        finish(c, auth, submit(c, auth, group, "A"))
        path = "/v1/plan/tasks/" + task["id"]
        assert c.get(path, headers=auth).json()["state"] == "started"
        assert c.post(path + "/complete", headers=auth).status_code == 409
        assert c.get("/v1/plan/today", headers=auth).json()["tasks"][0]["count"] == 2
        url = PRACTICE + "/" + planned["id"]
        current = c.get(url, headers=auth).json()
        # The unclassified slot was already graded through the notebook.
        assert current["position"] == 2
        finish(c, auth, submit(c, auth, current, "A"))
        assert c.get(path, headers=auth).json()["state"] == "done"
        with engine.connect() as db:
            assert (
                len(
                    db.execute(
                        select(answers).where(
                            answers.c.practice_id.in_([group["id"], planned["id"]])
                        )
                    ).all()
                )
                == 2
            )
