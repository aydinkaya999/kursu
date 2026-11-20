from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy import Engine, func, select, update
from test_accounts import Inbox
from test_plan import signin
from test_practice import TOPIC, guest

from app.core.http import ISTANBUL, server_now
from app.core.settings import Settings
from app.main import create_app
from app.modules.accounts.email_login import email_sender
from app.modules.commerce.models import counters, purchases
from app.modules.content.models import remote_config


def limited(response: Response, counter: str) -> None:
    assert response.status_code == 403 and response.json()["code"] == "free_limit_reached"
    assert response.json()["details"]["counter"] == counter


def account(
    c: TestClient, inbox: Inbox, auth: dict[str, str], email: str
) -> dict[str, str]:
    c.post("/v1/auth/email/start", headers=auth, json={"email": email}).raise_for_status()
    tokens = c.post(
        "/v1/auth/email/verify",
        headers=auth,
        json={"platform": "native", "email": email, "code": inbox.codes[email]},
    )
    tokens.raise_for_status()
    return {"Authorization": "Bearer " + tokens.json()["access_token"]}


def test_daily_lessons_questions_and_plan_use_istanbul_calendar(
    demo: Settings, engine: Engine
) -> None:
    app = create_app(demo)
    now = datetime(2027, 2, 1, 23, 59, tzinfo=ISTANBUL)
    with TestClient(app) as c:
        auth = signin(c)
        app.dependency_overrides[server_now] = lambda: now
        day = c.get("/v1/plan/today", headers=auth).json()
        task = "/v1/plan/tasks/" + day["tasks"][0]["id"]
        lessons = [i["id"] for i in c.get("/v1/lessons").json()[:2]]

        def read(id: str) -> Response:
            return c.get("/v1/lessons/" + id, headers=auth)

        assert c.get("/v1/lessons/" + lessons[0]).status_code == 401
        with ThreadPoolExecutor(2) as pool:
            responses = list(pool.map(read, lessons))
        assert sorted(r.status_code for r in responses) == [200, 403]
        used, waiting = lessons if responses[0].status_code == 200 else reversed(lessons)
        read(used).raise_for_status()
        limited(read(waiting), "lessons_per_day")
        limited(
            c.post(
                "/v1/practice-sessions",
                headers=auth,
                json={"kind": "lesson_check", "content_id": waiting},
            ),
            "lessons_per_day",
        )
        path = "/v1/practice-sessions"
        session = c.post(
            path, headers=auth, json={"kind": "topic_test", "content_id": TOPIC}
        ).json()
        url = path + "/" + session["id"]
        for i in range(5):
            q = session["question"]["id"]
            assert c.get(url, headers=auth).json()["question"]["id"] == q
            data = {
                "question_id": q,
                "selected_option": "A",
                "client_answer_id": str(uuid4()),
            }
            saved = c.post(url + "/answers", headers=auth, json=data).json()
            assert saved["feedback"]["rationales"][0]["option"] == "A"
            assert c.post(url + "/answers", headers=auth, json=data).json() == saved
            next_q = c.post(url + "/advance", headers=auth, json={"question_id": q})
            if i < 4:
                next_q.raise_for_status()
                session = next_q.json()
            else:
                limited(next_q, "questions_per_day")
                assert c.get(url, headers=auth).json()["feedback"]["question"]["id"] == q
                c.post(
                    "/v1/content-reports",
                    headers=auth,
                    json={"question_id": q, "text": "Örnek bildirim"},
                ).raise_for_status()
        with engine.connect() as db:
            assert (
                db.scalar(
                    select(counters.c["count"]).where(
                        counters.c.counter == "questions_per_day"
                    )
                )
                == 5
            )
        now += timedelta(minutes=1)
        read(waiting).raise_for_status()
        c.post(url + "/advance", headers=auth, json={"question_id": q}).raise_for_status()
        now += timedelta(days=1)
        c.get("/v1/plan/today", headers=auth).raise_for_status()
        now += timedelta(days=1)
        limited(c.get("/v1/plan/today", headers=auth), "plan_days")
        limited(c.get(task, headers=auth), "plan_days")
        limited(c.post(task + "/start", headers=auth), "plan_days")
        progress = c.get("/v1/progress", headers=auth).json()
        assert (
            not progress["detailed"] and not progress["history"] and not progress["trend"]
        )
        assert len(progress["sections"]) == 6 and all(
            not s["topics"] for s in progress["sections"]
        )
        assert progress["streak"] == 0 and progress["weekly_goal"] == 5
        c.get("/v1/notebook", headers=auth).raise_for_status()
        assert (
            c.post(path, headers=auth, json={"kind": "review", "mode": "early"}).json()[
                "code"
            ]
            == "entitlement_required"
        )


def test_season_mock_allowance_and_last_blank_are_earned_once(
    demo: Settings, engine: Engine
) -> None:
    with TestClient(create_app(demo)) as c:
        auth = guest(c)
        exams = c.get("/v1/mocks").json()

        def start(exam: str, mode: str) -> Response:
            return c.post(
                "/v1/mocks/" + exam + "/attempts", headers=auth, json={"mode": mode}
            )

        first = start(exams[0]["id"], "practice").json()
        assert start(exams[0]["id"], "practice").json()["id"] == first["id"]
        limited(start(exams[1]["id"], "timed"), "mock_exams")
        c.post(
            "/v1/mock-attempts/" + first["id"] + "/submit", headers=auth
        ).raise_for_status()
        limited(start(exams[0]["id"], "practice"), "mock_exams")
        c.get(
            "/v1/mock-attempts/" + first["id"] + "/review", headers=auth
        ).raise_for_status()
        with engine.begin() as db:
            db.execute(
                update(remote_config)
                .where(remote_config.c.key == "free_limits")
                .values(
                    value=dict(
                        plan_days=3, lessons_per_day=1, questions_per_day=1, mock_exams=1
                    )
                )
            )
        state = c.post(
            "/v1/practice-sessions",
            headers=auth,
            json={"kind": "topic_test", "content_id": TOPIC},
        ).json()
        path = "/v1/practice-sessions/" + state["id"]
        data = {
            "client_answer_id": str(uuid4()),
            "question_id": state["question"]["id"],
            "selected_option": None,
        }
        limited(c.post(path + "/answers", headers=auth, json=data), "questions_per_day")
        limited(c.get(path, headers=auth), "questions_per_day")
        limited(c.post(path + "/answers", headers=auth, json=data), "questions_per_day")


def test_balanced_persistent_quotes_and_guest_merge(demo: Settings, engine: Engine) -> None:
    inbox = Inbox()
    app = create_app(demo)
    app.dependency_overrides[email_sender] = lambda: inbox
    with TestClient(app) as c:
        guests = [guest(c) for _ in range(9)]

        def quote(auth: dict[str, str]) -> int:
            return int(c.get("/v1/paywall", headers=auth).json()["amount_try"])

        with ThreadPoolExecutor(4) as pool:
            amounts = list(pool.map(quote, guests))
        assert Counter(amounts) == {790: 3, 990: 3, 1290: 3}
        with engine.begin() as db:
            db.execute(
                update(remote_config)
                .where(remote_config.c.key == "web_price_groups_try")
                .values(value=[100, 200, 300])
            )
        assert [quote(auth) for auth in guests] == amounts
        auth = account(c, inbox, guests[0], "candidate@example.org")
        assert quote(auth) == amounts[0]
        other = guests[1]
        lessons = c.get("/v1/lessons").json()
        c.get("/v1/lessons/" + lessons[0]["id"], headers=other).raise_for_status()
        merged = account(c, inbox, other, "candidate@example.org")
        assert quote(merged) == amounts[0]
        limited(c.get("/v1/lessons/" + lessons[1]["id"], headers=merged), "lessons_per_day")
        assert c.get("/v1/entitlements").status_code == 401


@pytest.mark.parametrize("platform", ["web", "ios", "android"])
def test_development_checkout_cross_platform_expiry_and_replay(
    demo: Settings, engine: Engine, platform: str
) -> None:
    inbox = Inbox()
    app = create_app(demo)
    app.dependency_overrides[email_sender] = lambda: inbox
    with TestClient(app) as c:
        anon = guest(c)
        assert (
            c.post("/v1/purchases/web/checkout", headers=anon).json()["code"]
            == "account_required"
        )
        auth = account(c, inbox, anon, "owner@example.org")
        other = account(c, inbox, guest(c), "second@example.org")
        now = datetime(2027, 6, 11, 23, 59, tzinfo=ISTANBUL)
        app.dependency_overrides[server_now] = lambda: now
        offer = c.get("/v1/paywall", headers=auth, params={"platform": platform}).json()

        def buy() -> Response:
            if platform == "web":
                return c.post("/v1/purchases/web/checkout", headers=auth)
            return c.post(
                "/v1/purchases/native/verify",
                headers=auth,
                json={"platform": platform, "receipt": offer["sandbox_receipt"]},
            )

        if platform != "web":
            invalid = c.post(
                "/v1/purchases/native/verify",
                headers=other,
                json={"platform": platform, "receipt": offer["sandbox_receipt"]},
            )
            assert invalid.status_code == 422
            assert (
                c.post(
                    "/v1/purchases/native/verify",
                    headers=auth,
                    json={
                        "platform": "ios" if platform == "android" else "android",
                        "receipt": offer["sandbox_receipt"],
                    },
                ).status_code
                == 422
            )
        with ThreadPoolExecutor(2) as pool:
            ordered = list(pool.map(lambda _: buy().json(), range(2)))
        assert (
            ordered[0]
            == ordered[1]
            == {"active": True, "source": platform, "valid_until": "2027-06-11"}
        )
        for device in ("web", "ios", "android"):
            assert (
                c.get("/v1/paywall", headers=auth, params={"platform": device}).json()[
                    "access"
                ]
                == ordered[0]
            )
        assert not c.get("/v1/entitlements", headers=other).json()["active"]
        with engine.connect() as db:
            assert db.scalar(select(func.count()).select_from(purchases)) == 1
        assert c.get("/v1/progress", headers=auth).json()["detailed"]
        for lesson in c.get("/v1/lessons").json()[:2]:
            c.get("/v1/lessons/" + lesson["id"], headers=auth).raise_for_status()
        now += timedelta(minutes=1)
        assert not c.get("/v1/entitlements", headers=auth).json()["active"]
        assert buy().status_code == 409


def test_production_never_accepts_sandbox_purchases(demo: Settings) -> None:
    app = create_app(demo.model_copy(update={"app_env": "production"}))
    inbox = Inbox()
    app.dependency_overrides[email_sender] = lambda: inbox
    with TestClient(app) as c:
        auth = account(c, inbox, guest(c), "candidate@example.org")
        app.dependency_overrides[server_now] = lambda: datetime(2027, 2, 1, tzinfo=ISTANBUL)
        for platform in ("web", "ios", "android"):
            offer = c.get("/v1/paywall", headers=auth, params={"platform": platform}).json()
            assert not offer["checkout_available"] and offer["sandbox_receipt"] is None
        assert c.post("/v1/purchases/web/checkout", headers=auth).status_code == 503
        assert (
            c.post(
                "/v1/purchases/native/verify",
                headers=auth,
                json={"platform": "ios", "receipt": "test"},
            ).status_code
            == 503
        )


def test_migration_restores_existing_mock_lesson_and_question_usage(
    demo: Settings, engine: Engine
) -> None:
    from pathlib import Path

    from alembic import command
    from alembic.config import Config

    migration = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    with TestClient(create_app(demo)) as c:
        auth = guest(c)
        exam = c.get("/v1/mocks").json()[0]["id"]
        path = "/v1/mocks/" + exam + "/attempts"
        c.post(path, headers=auth, json={"mode": "timed"}).raise_for_status()
        lesson = c.get("/v1/lessons").json()[0]["id"]
        c.post(
            "/v1/practice-sessions",
            headers=auth,
            json={"kind": "lesson_check", "content_id": lesson},
        ).raise_for_status()
        state = c.post(
            "/v1/practice-sessions",
            headers=auth,
            json={"kind": "topic_test", "content_id": TOPIC},
        ).json()
        c.post(
            "/v1/practice-sessions/" + state["id"] + "/answers",
            headers=auth,
            json={
                "question_id": state["question"]["id"],
                "client_answer_id": str(uuid4()),
                "selected_option": None,
            },
        ).raise_for_status()
        command.downgrade(migration, "0008_mock")
        command.upgrade(migration, "head")
        with engine.connect() as db:
            counts = dict(
                db.execute(select(counters.c.counter, counters.c["count"])).tuples().all()
            )
        assert counts == {"lessons_per_day": 1, "questions_per_day": 2, "mock_exams": 1}
        limited(c.post(path, headers=auth, json={"mode": "practice"}), "mock_exams")
