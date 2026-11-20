import asyncio
from collections import Counter
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import Engine, func, select, update
from test_plan import signin

from app.core.db import Database
from app.core.http import ISTANBUL, server_now
from app.core.settings import Settings
from app.main import create_app
from app.modules.content.models import questions, subtests, topics
from app.modules.mocks.service import net, submit_expired
from app.modules.placement.models import answers


def test_quarter_scoring() -> None:
    assert [net(0, 1), net(1, 1), net(4, 4), net(80, 0)] == [-0.25, 0.75, 3, 80]


def test_mock_navigation_grading_withdrawal_and_progress(
    demo: Settings, engine: Engine
) -> None:
    app = create_app(demo)
    now = datetime(2027, 2, 7, 12, tzinfo=ISTANBUL)
    with TestClient(app) as c:
        auth = signin(c)
        other = signin(c, False)
        app.dependency_overrides[server_now] = lambda: now
        listed = c.get("/v1/mocks").json()
        assert len(listed) == 10
        plan = c.get("/v1/plan/today", headers=auth).json()
        exam = plan["tasks"][0]["content_id"]
        start = "/v1/mocks/" + exam + "/attempts"
        a = c.post(start, headers=auth, json={"mode": "practice"}).json()
        path = "/v1/mock-attempts/" + a["id"]
        assert a["remaining_seconds"] is a["deadline_at"] is None
        with engine.connect() as db:
            counts = dict(
                db.execute(
                    select(subtests.c.short_name, subtests.c.question_count).order_by(
                        subtests.c.exam_order
                    )
                )
                .tuples()
                .all()
            )
            total_topics = db.scalar(select(func.count()).select_from(topics))
        assert [i["subtest"] for i in a["questions"]] == [
            s for s, n in counts.items() for _ in range(n)
        ]
        ids = [i["question"]["id"] for i in a["questions"]]
        assert len(set(ids)) == 80 and set(a["questions"][0]["question"]) == {
            "id",
            "stem",
            "options",
        }
        assert c.get(path + "/review", headers=auth).status_code == 409
        assert c.get(path + "/result", headers=auth).status_code == 409
        assert c.get(path, headers=other).status_code == 404
        with engine.begin() as db:
            correct = dict(
                db.execute(
                    select(questions.c.id, questions.c.correct_option).where(
                        questions.c.id.in_(ids)
                    )
                )
                .tuples()
                .all()
            )
        wrong = next(x for x in "ABCDE" if x != correct[ids[1]])
        for pos, choice in [
            (0, "B"),
            (0, correct[ids[0]]),
            (1, wrong),
            (2, "C"),
            (2, None),
        ]:
            c.put(
                path + "/answers/" + ids[pos],
                headers=auth,
                json={"selected_option": choice},
            ).raise_for_status()
        c.put(
            path + "/answers/" + ids[1], headers=auth, json={"flagged": True}
        ).raise_for_status()
        c.put(path + "/position", headers=auth, json={"position": 17}).raise_for_status()
        now += timedelta(hours=4)
        resumed = c.post(start, headers=auth, json={"mode": "practice"}).json()
        assert resumed["id"] == a["id"] and resumed["position"] == 17
        assert (
            resumed["questions"][1]["selected_option"] == wrong
            and resumed["questions"][1]["flagged"]
        )
        with engine.begin() as db:
            assert db.scalar(select(func.count()).select_from(answers)) == 0
            db.execute(
                update(questions)
                .where(questions.c.id == ids[-1])
                .values(status="quarantined")
            )
        assert c.get(path, headers=auth).json()["questions"][-1]["question"] is None
        r = c.post(path + "/submit", headers=auth).json()
        assert (
            r
            == c.post(path + "/submit", headers=auth).json()
            == c.get(path + "/result", headers=auth).json()
        )
        assert (r["used_minutes"], r["total"], r["withdrawn"]) == (240, 79, 1)
        assert (r["net"], r["correct"], r["wrong"], r["blank"]) == (0.75, 1, 1, 77)
        assert (
            r["sections"][0]["net"] == 0.75
            and sum(s["net"] for s in r["sections"]) == r["net"]
        )
        assert len(r["sections"]) == 6 and r["wrong_topics"][0]["count"] == 1
        review = c.get(path + "/review", headers=auth).json()
        assert len(review) == 79 and review[1]["rationales"][0]["option"] == wrong
        assert review[15]["steps"] and review[15]["source"]
        assert c.get("/v1/plan/today", headers=auth).json()["done"] == 1
        assert c.get("/v1/notebook/summary", headers=auth).json()["open_count"] == 1
        d = c.get("/v1/progress", headers=auth).json()
        assert d["net_range"]["low"] <= d["net_range"]["high"] and len(d["sections"]) == 6
        states = Counter(t["state"] for s in d["sections"] for t in s["topics"])
        assert (
            sum(states.values()) == total_topics
            and states["not_started"]
            and states["in_progress"]
        )
        assert d["history"] == c.get("/v1/mock-history", headers=auth).json()
        assert d["history"][0]["net"] == 0.75 and d["trend"] == []
        with engine.begin() as db:
            db.execute(
                update(questions)
                .where(questions.c.id == ids[-1])
                .values(status="published")
            )
        now += timedelta(days=8)
        second = c.post(
            "/v1/mocks/" + listed[-1]["id"] + "/attempts",
            headers=auth,
            json={"mode": "practice"},
        ).json()
        p = "/v1/mock-attempts/" + second["id"]
        c.put(
            p + "/answers/" + second["questions"][0]["question"]["id"],
            headers=auth,
            json={"selected_option": "B"},
        ).raise_for_status()
        c.post(p + "/submit", headers=auth).raise_for_status()
        assert len(c.get("/v1/progress", headers=auth).json()["trend"]) == 2
        now += timedelta(days=21)
        assert c.get("/v1/progress", headers=auth).json()["net_change"] is not None


def test_expiry_is_server_owned_and_job_is_idempotent(demo: Settings) -> None:
    now = datetime(2027, 2, 1, 10, tzinfo=ISTANBUL)
    app = create_app(demo)

    async def job() -> int:
        database = Database(demo.database_url)
        try:
            async with database.sessions() as db:
                return await submit_expired(db, now)
        finally:
            await database.engine.dispose()

    with TestClient(app) as c:
        auth = signin(c, False)
        app.dependency_overrides[server_now] = lambda: now
        exams = c.get("/v1/mocks").json()
        attempts = [
            c.post(
                "/v1/mocks/" + m["id"] + "/attempts", headers=auth, json={"mode": "timed"}
            ).json()
            for m in exams[:2]
        ]
        a, b = attempts
        path = "/v1/mock-attempts/" + a["id"]
        assert a["remaining_seconds"] == 6600
        now += timedelta(minutes=109)
        assert c.get(path, headers=auth).json()["remaining_seconds"] == 60
        now += timedelta(minutes=5)
        late = c.put(
            path + "/answers/" + a["questions"][0]["question"]["id"],
            headers=auth,
            json={"selected_option": "A"},
        ).json()
        assert late["submitted_at"] == a["deadline_at"] and late["blank"] == 80
        assert asyncio.run(job()) == 1 and asyncio.run(job()) == 0
        frozen = c.get("/v1/mock-attempts/" + b["id"] + "/result", headers=auth).json()
        assert frozen["used_minutes"] == 110 and frozen["submitted_at"] == b["deadline_at"]
