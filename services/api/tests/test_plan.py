from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, select, update
from study_support import finish_task, grant_pass

from app.core.http import ISTANBUL, server_now
from app.core.settings import Settings
from app.main import create_app
from app.modules.content.models import lessons, questions
from app.modules.plan.models import plans, tasks
from app.modules.plan.rules import DAY, Topic, build, distribute, streak, weight
from app.modules.plan.schemas import Assignment

MON = date(2027, 2, 1)
EXAM = date(2027, 5, 8)


def sample(id: str, importance: int, m: float, opened: bool = False) -> Topic:
    return Topic(id, id, id, importance, m, opened, [(id, id)], 30)


def schedule(
    day: date = MON, budget: int = 60, due: int = 0, **options: Any
) -> list[Assignment]:
    args: dict[str, Any] = dict(
        day=day,
        exam=EXAM,
        minutes=budget,
        score_type="P1",
        mock_weekday=6,
        due=[str(i) for i in range(due)],
        topics=[
            sample("weak", 25, 0.1),
            sample("strong", 25, 0.9),
            sample("lower", 15, 0.15),
        ],
        mock=("mock", "mock"),
        kept=[],
    )
    args.update(options)
    return build(**args)


@pytest.mark.parametrize("minutes", [30, 60, 90])
@pytest.mark.parametrize("due", [0, 6, 200])
def test_plan_2_to_6_order_caps_weights_and_costs(minutes: int, due: int) -> None:
    jobs = schedule(budget=minutes, due=due)
    assert sum(t.quarters for t in jobs) <= minutes * 4
    if due:
        r = jobs[0]
        assert r.kind == "review" and r.count == min(due, minutes * 4 * 2 // 5 // 5)
        assert r.quarters == r.count * 5 and r.quarters <= minutes * 4 * 0.4
    lessons = [t for t in jobs if t.kind == "lesson"]
    assert [t.topic_id for t in lessons] == ["weak", "lower"]
    assert all(t.quarters == 20 for t in lessons)
    tests = [t for t in jobs if t.kind == "topic_test"]
    if tests:
        t = tests[0]
        assert t.topic_id == "weak" and 10 <= t.count <= 15 and t.quarters == t.count * 6
        assert jobs[-1] == t
    assert weight(25, "P1") == 25 and weight(25, "P2") == weight(25, "P3") == 12.5


def test_plan_4_7_9_exam_boundary_mock_exception_and_redistribution() -> None:
    topics = [sample("new", 25, 0), sample("opened", 10, 0.4, True)]
    assert any(t.topic_id == "new" for t in schedule(EXAM - DAY * 31, topics=topics))
    near = schedule(EXAM - DAY * 30, due=2, topics=topics)
    assert [t.kind for t in near] == ["review", "topic_test"] and near[
        -1
    ].topic_id == "opened"
    assert schedule(EXAM - DAY * 30, topics=[topics[0]]) == []
    for budget in (30, 60, 90):
        sunday = schedule(MON + DAY * 6, budget, 200)
        assert len(sunday) == 1 and sunday[0].kind == "mock" and sunday[0].quarters == 440
    assert schedule(EXAM) == []
    dates = [d for d in distribute(MON, 6, [EXAM] * 4) if d is not None]
    assert dates[0] == MON and len(set(dates)) == 4 and max(dates) < EXAM
    assert all(d.weekday() != 6 for d in dates)
    short = schedule(carry=("lesson", "strong"))
    assert short[0].content_id == "strong" and len(short) == len(schedule())


def test_strk_1_to_4_monday_week_freeze_reset_and_weekly_goal() -> None:
    # A missed day freezes automatically. Today's unfinished day remains open.
    assert streak(MON, MON + DAY * 2, [MON]).current == 1
    assert streak(MON, MON + DAY * 3, [MON]).current == 0
    s = streak(
        MON,
        MON + DAY * 7,
        [MON, MON + DAY * 2, MON + DAY * 3, MON + DAY * 4, MON + DAY * 5, MON + DAY * 6],
    )
    assert s.current == s.longest == 6 and s.weekly_done == 0
    s = streak(MON, MON + DAY * 8, [MON + DAY * i for i in (0, 2, 3, 4, 5, 6, 8)])
    assert s.current == 7 and s.weekly_done == 1 and s.freeze_used_week == MON + DAY * 7
    assert streak(MON, MON + DAY * 6, [MON + DAY * i for i in range(7)]).weekly_done == 5
    assert streak(MON, MON, []).current == 0


def signin(client: TestClient, data: bool = True) -> dict[str, str]:
    session = client.post("/v1/auth/guest", json={"platform": "native"}).json()
    auth = {"Authorization": "Bearer " + session["access_token"]}
    if data:
        client.patch(
            "/v1/me/profile",
            headers=auth,
            json={
                "field_id": "sinif-ogretmenligi",
                "daily_minutes": 60,
                "attempt_kind": "first",
            },
        ).raise_for_status()
    return auth


def test_plan_1_8_10_tasks_dates_and_streak(demo: Settings, engine: Engine) -> None:
    app = create_app(demo)
    with TestClient(app) as c:
        user = signin(c)
        grant_pass(c, user, engine, date.max)
        other = signin(c, False)
        now = datetime(2027, 2, 1, 11, tzinfo=ISTANBUL)
        app.dependency_overrides[server_now] = lambda: now

        def today() -> dict[str, Any]:
            response = c.get("/v1/plan/today", headers=user)
            response.raise_for_status()
            return dict(response.json())

        assert c.get("/v1/plan/today").status_code == 401
        assert c.get("/v1/plan/today", headers=other).status_code == 409
        day = today()
        assert (
            day["plan_date"] == MON.isoformat() and day["days_to_exam"] == (EXAM - MON).days
        )
        assert day == today() and day["total"] == 3 and day["done"] == 0
        job = day["tasks"][0]
        path = "/v1/plan/tasks/" + job["id"]
        assert c.get(path, headers=user).json()["id"] == job["id"]
        assert c.get(path, headers=other).status_code == 404
        assert c.post(path + "/complete", headers=user).status_code == 409
        assert c.post(path + "/start", headers=user).json()["state"] == "started"
        assert c.post(path + "/complete", headers=user).status_code == 409
        finish_task(c, user, job)
        with ThreadPoolExecutor(max_workers=2) as pool:
            assert [
                r.status_code
                for r in pool.map(
                    lambda _: c.post(path + "/complete", headers=user), range(2)
                )
            ] == [200, 200]
        revised = c.patch(
            "/v1/me/settings",
            headers=user,
            json={"daily_minutes": 30, "notification_time": None},
        )
        revised.raise_for_status()
        with engine.connect() as db:
            assert db.scalar(select(plans.c.daily_minutes)) == 30
        day = today()
        assert day["tasks"][0]["id"] == job["id"] and day["done"] == 1
        assert sum(t["minutes"] for t in day["tasks"]) <= 30
        assert sum(t["is_next"] for t in day["tasks"]) == 1
        for t in day["tasks"]:
            finish_task(c, user, t)
        result = today()
        assert (
            result["done"] == result["total"]
            and result["streak"] == result["weekly_done"] == 1
            and result["percent"] == 100
        )
        assert result["remaining_minutes"] == 0 and not any(
            t["is_next"] for t in result["tasks"]
        )
        now = datetime(2027, 2, 1, 20, 59, 59, tzinfo=UTC)
        assert today()["plan_date"] == "2027-02-01"
        now += timedelta(seconds=1)
        tomorrow = today()
        assert (
            tomorrow["plan_date"] == "2027-02-02"
            and tomorrow["done"] == 0
            and tomorrow["streak"] == 1
        )
        old = tomorrow["tasks"][0]["id"]
        now += DAY
        after = today()
        assert after["streak"] == 1 and sum(t["minutes"] for t in after["tasks"]) <= 30
        missed_work = {(t["kind"], t["content_id"]) for t in tomorrow["tasks"]}
        todays_work = {(t["kind"], t["content_id"]) for t in after["tasks"]}
        assert len(missed_work & todays_work) == 1
        assert c.post(f"/v1/plan/tasks/{old}/start", headers=user).status_code == 409
        with engine.connect() as db:
            dates = db.scalars(
                select(tasks.c.carry_on).where(tasks.c.carry_on.is_not(None))
            ).all()
            assert len(set(dates)) >= 2 and min(dates) == date(2027, 2, 3)
        now += DAY
        assert today()["streak"] == 0
        now = datetime(2027, 2, 7, 8, tzinfo=ISTANBUL)
        sunday = today()
        assert sunday["mock_day"] and [t["minutes"] for t in sunday["tasks"]] == [110]


def test_plan_2_3_7_due_reviews_use_real_guest_history(
    demo: Settings, engine: Engine
) -> None:
    app = create_app(demo)
    with TestClient(app) as c:
        user = signin(c)
        clock = datetime(2027, 4, 7, 8, tzinfo=ISTANBUL)
        app.dependency_overrides[server_now] = lambda: clock
        attempt = c.post("/v1/placement", headers=user, json={}).json()
        item = attempt["question"]
        with engine.connect() as db:
            right = db.scalar(
                select(questions.c.correct_option).where(questions.c.id == item["id"])
            )
        data = {
            "client_answer_id": str(uuid4()),
            "question_id": item["id"],
            "selected_option": right,
            "not_sure": True,
        }
        c.post(
            f"/v1/placement/{attempt['id']}/answers", headers=user, json=data
        ).raise_for_status()
        clock += DAY
        day = c.get("/v1/plan/today", headers=user).json()
        assert [t["kind"] for t in day["tasks"]] == ["review", "topic_test"]
        first = day["tasks"][0]
        assert first["minutes"] == 1.25 and first["count"] == 1
        assert day["days_to_exam"] == 30
        path = f"/v1/plan/tasks/{first['id']}"
        assert c.post(path + "/start", headers=user).status_code == 403
        grant_pass(c, user, engine, EXAM)
        assert c.post(path + "/complete", headers=user).status_code == 409
        state = c.post(
            "/v1/practice-sessions",
            headers=user,
            json={"kind": "review", "task_id": first["id"]},
        ).json()
        assert state["question"]["id"] != item["id"]
        url = "/v1/practice-sessions/" + state["id"]
        with engine.connect() as db:
            right = db.scalar(
                select(questions.c.correct_option).where(
                    questions.c.id == state["question"]["id"]
                )
            )
        graded = c.post(
            url + "/answers",
            headers=user,
            json={
                "question_id": state["question"]["id"],
                "client_answer_id": str(uuid4()),
                "selected_option": right,
            },
        )
        graded.raise_for_status()
        assert graded.json()["feedback"]["is_correct"]
        c.post(
            url + "/advance", headers=user, json={"question_id": state["question"]["id"]}
        ).raise_for_status()
        c.post(url + "/finish", headers=user).raise_for_status()
        assert c.get(path, headers=user).json()["state"] == "done"
        clock += DAY
        assert not any(
            t["kind"] == "review"
            for t in c.get("/v1/plan/today", headers=user).json()["tasks"]
        )


def test_plan_8_downsizing_preserves_earned_work_and_limits_review_share() -> None:
    done = Assignment(
        kind="review", count=20, objectives=[str(i) for i in range(20)], quarters=100
    )
    adjusted = schedule(budget=30, kept=[done])
    assert done not in adjusted
    assert sum(t.quarters for t in adjusted) <= 30 * 4 - done.quarters


def test_merged_completions_keep_one_mock_and_two_daily_lesson_slots() -> None:
    sunday = MON + DAY * 6
    first = schedule(sunday)[0]
    second = first.model_copy(update={"content_id": "another-mock"})
    assert schedule(sunday, kept=[first, second], closed=True) == [first]
    lessons = [
        Assignment(kind="lesson", topic_id=t, content_id=t, quarters=20)
        for t in ("a", "b", "c")
    ]
    assert schedule(kept=lessons, closed=True) == lessons[:2]


def test_plan_9_deferred_tasks_return_on_their_assigned_dates(
    demo: Settings, engine: Engine
) -> None:
    app = create_app(demo)
    with TestClient(app) as c:
        auth = signin(c)
        grant_pass(c, auth, engine, date.max)
        clock = datetime(2027, 2, 1, 9, tzinfo=ISTANBUL)
        app.dependency_overrides[server_now] = lambda: clock

        def assignments() -> list[dict[str, Any]]:
            response = c.get("/v1/plan/today", headers=auth)
            response.raise_for_status()
            return list(response.json()["tasks"])

        missed_keys = {(t["kind"], t["content_id"]) for t in assignments()}
        clock += DAY
        assignments()
        with engine.connect() as db:
            slots = {
                row.carry_on: (row.type, row.ref["content_id"])
                for row in db.execute(
                    select(tasks.c.carry_on, tasks.c.type, tasks.c.ref).where(
                        tasks.c.carry_on.is_not(None)
                    )
                )
            }
        assert len(slots) == len(missed_keys) == 3 and min(slots) == clock.date()
        c.patch(
            "/v1/me/settings",
            headers=auth,
            json={"daily_minutes": 30, "notification_time": None},
        ).raise_for_status()
        for scheduled_date, key in sorted(slots.items()):
            clock = datetime.combine(scheduled_date, clock.timetz())
            work = assignments()
            assert {(t["kind"], t["content_id"]) for t in work} & missed_keys == {key}
            assert sum(t["minutes"] for t in work) <= 30
            for job in work:
                finish_task(c, auth, job)


def test_withdrawn_lesson_is_replaced_before_start(demo: Settings, engine: Engine) -> None:
    app = create_app(demo)
    with TestClient(app) as c:
        auth = signin(c)
        app.dependency_overrides[server_now] = lambda: datetime(
            2027, 2, 1, 9, tzinfo=ISTANBUL
        )
        original = c.get("/v1/plan/today", headers=auth).json()
        first = next(task for task in original["tasks"] if task["kind"] == "lesson")
        with engine.begin() as db:
            db.execute(
                update(lessons)
                .where(lessons.c.id == first["content_id"])
                .values(status="quarantined")
            )
        assert (
            c.post(f"/v1/plan/tasks/{first['id']}/start", headers=auth).status_code == 409
        )
        current = c.get("/v1/plan/today", headers=auth).json()
        assert current["total"] == original["total"]
        assert first["id"] not in {task["id"] for task in current["tasks"]}
