from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, time, timedelta
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, func, select, update

from app.core.http import ISTANBUL, server_now
from app.core.settings import Settings
from app.main import create_app
from app.modules.accounts.security import COOKIE
from app.modules.content.models import questions, remote_config
from app.modules.placement.models import answers, attempts
from app.modules.placement.schemas import Kind
from app.modules.placement.service import estimate, next_level, sequence

PROFILE = {"field_id": "sinif-ogretmenligi", "daily_minutes": 60, "attempt_kind": "first"}


def guest(client: TestClient) -> dict[str, str]:
    tokens = client.post("/v1/auth/guest", json={"platform": "native"})
    assert tokens.status_code == 200
    return {"Authorization": "Bearer " + tokens.json()["access_token"]}


def test_onb_1_silent_web_and_native_guests_keep_their_identity(seeded: Settings) -> None:
    with TestClient(create_app(seeded), base_url="https://testserver") as client:
        assert client.get("/v1/me").status_code == 401
        response = client.post("/v1/auth/guest", json={"platform": "web"})
        assert set(response.json()) == {"access_token"}
        cookie = response.headers["set-cookie"].lower()
        assert all(flag in cookie for flag in ("httponly", "secure", "samesite=lax"))

        def identity(access: str) -> str:
            me = client.get("/v1/me", headers={"Authorization": "Bearer " + access}).json()
            assert me["is_guest"]
            return str(me["id"])

        web = identity(response.json()["access_token"])
        assert (
            identity(
                client.post("/v1/auth/guest", json={"platform": "web"}).json()[
                    "access_token"
                ]
            )
            == web
        )
        native = client.post("/v1/auth/guest", json={"platform": "native"}).json()
        assert identity(native["access_token"]) != web
        body = {"platform": "native", "refresh_token": native["refresh_token"]}
        refreshed = client.post("/v1/auth/refresh", json=body).json()
        assert identity(refreshed["access_token"]) == identity(native["access_token"])
        assert refreshed["refresh_token"] != native["refresh_token"]
        assert client.post("/v1/auth/refresh", json=body).status_code == 401
        assert (
            client.post("/v1/auth/refresh", json={"platform": "native"}).status_code == 401
        )
        assert client.cookies.get(COOKIE) is not None


def test_onb_2_profile_validates_choices_and_derives_score_type(seeded: Settings) -> None:
    with TestClient(create_app(seeded)) as client:
        auth = guest(client)
        assert client.get("/v1/me", headers=auth).json()["profile"] is None
        assert client.post("/v1/placement", headers=auth, json={}).status_code == 409
        for invalid in (
            {"field_id": "unknown"},
            {"daily_minutes": 45},
            {"attempt_kind": "unknown"},
            {"score_type": "P1"},
        ):
            resp = client.patch("/v1/me/profile", headers=auth, json={**PROFILE, **invalid})
            assert resp.status_code == 422
            assert resp.json()["code"] == "validation_error"
        for field, score in (
            ("sinif-ogretmenligi", "P2"),
            ("ingilizce-ogretmenligi", "P3"),
        ):
            profile = {
                **PROFILE,
                "field_id": field,
                "daily_minutes": 90,
                "attempt_kind": "repeat",
            }
            resp = client.patch("/v1/me/profile", headers=auth, json=profile)
            assert resp.status_code == 200
            assert resp.json() == {**profile, "score_type": score}
            assert client.get("/v1/me", headers=auth).json()["profile"] == resp.json()


def test_onb_4_countdown_uses_remote_config_and_istanbul_midnight(
    seeded: Settings, engine: Engine
) -> None:
    app = create_app(seeded)
    with engine.begin() as conn:
        conn.execute(
            update(remote_config)
            .where(remote_config.c.key == "exam_date")
            .values(value="2027-05-09")
        )
    with TestClient(app) as client:
        for now, expected, seconds in (
            ("2027-05-07T20:59:59+00:00", 2, 1),
            ("2027-05-07T20:59:59.800000+00:00", 2, 1),
            ("2027-05-07T21:00:00+00:00", 1, 86400),
            ("2027-05-08T21:00:00+00:00", 0, 86400),
            ("2027-05-10T00:00:00+00:00", 0, 75600),
        ):
            app.dependency_overrides[server_now] = lambda now=now: datetime.fromisoformat(
                now
            )
            response = client.get("/v1/config")
            assert response.status_code == 200
            data = response.json()
            assert data["days_to_exam"] == expected
            assert data["seconds_to_midnight"] == seconds
            assert data["exam_date"] == "2027-05-09"
            assert datetime.fromisoformat(data["server_now"]) == datetime.fromisoformat(now)


def test_plc_1_plc_2_quotas_and_level_boundaries() -> None:
    assert Counter(sequence("full")) == {
        "education": 11,
        "verbal": 6,
        "quantitative": 6,
        "legislation": 3,
        "history": 2,
        "geography": 2,
    }
    assert len(sequence("short")) == 10 and len(set(sequence("short"))) == 6
    assert [next_level(level, True) for level in (1, 2, 3)] == [2, 3, 3]
    assert [next_level(level, False) for level in (1, 2, 3)] == [1, 1, 2]
    assert [next_level(level, None) for level in (1, 2, 3)] == [1, 2, 3]


def test_d_1_estimate_smoothing_weighting_rounding_and_clamping() -> None:
    assert estimate({"a": 80}, {}, {}) == (27, 33)
    assert estimate({"a": 80}, {"a": 9}, {"a": 10}) == (57, 70)
    assert estimate({"a": 80}, {"a": 0}, {"a": 200}) == (0, 0)
    assert estimate({"a": 80}, {"a": 200}, {"a": 200}) == (72, 80)
    assert estimate({"a": 60, "b": 20}, {"a": 1, "b": 0}, {"a": 2, "b": 3}) == (20, 26)


def test_plc_3_to_7_and_why_6_guest_completes_resumes_and_retakes(
    demo: Settings, engine: Engine
) -> None:
    app = create_app(demo)
    with TestClient(app) as client, engine.connect() as conn:
        auth = guest(client)
        stranger = guest(client)
        client.patch("/v1/me/profile", json=PROFILE, headers=auth).raise_for_status()

        def start(kind: Kind = "full") -> dict[str, Any]:
            response = client.post("/v1/placement", json={"kind": kind}, headers=auth)
            response.raise_for_status()
            return dict(response.json())

        initial = start()
        assert initial["total"] == 30 and initial["position"] == 1
        assert start() == initial
        attempt_id = initial["id"]
        post = f"/v1/placement/{attempt_id}/answers"
        result_url = f"/v1/placement/{attempt_id}/result"
        assert client.get(result_url, headers=auth).status_code == 409
        assert client.get(result_url, headers=stranger).status_code == 404
        assert client.get("/v1/plan/first-week", headers=auth).status_code == 404
        attempt = initial
        cases: list[tuple[Kind, int]] = [("full", 30), ("short", 10)]
        for kind, total in cases:
            if kind == "short":
                assert (
                    client.post(
                        "/v1/placement", json={"kind": kind}, headers=auth
                    ).status_code
                    == 409
                )
                midnight = datetime.combine(
                    datetime.now(ISTANBUL).date(), time.min, ISTANBUL
                )
                with engine.begin() as write:
                    write.execute(
                        update(attempts).values(
                            completed_at=midnight - timedelta(days=14) + timedelta(hours=23)
                        )
                    )
                    write.execute(
                        update(answers).values(
                            answered_at=datetime.now(UTC) - timedelta(days=29)
                        )
                    )
                app.dependency_overrides[server_now] = lambda now=midnight: (
                    now - timedelta(microseconds=1)
                )
                assert not client.get("/v1/me", headers=auth).json()["placement"][
                    "can_retake"
                ]
                app.dependency_overrides[server_now] = lambda now=midnight: now
                assert client.get("/v1/me", headers=auth).json()["placement"]["can_retake"]
                attempt = start("short")
                del app.dependency_overrides[server_now]
                attempt_id = attempt["id"]
                post = f"/v1/placement/{attempt_id}/answers"
                result_url = f"/v1/placement/{attempt_id}/result"
            levels = dict.fromkeys(sequence(kind), 2)
            asked: Counter[str] = Counter()
            answered: Counter[str] = Counter()
            correct: Counter[str] = Counter()
            ids: set[str] = set()
            for step in range(total):
                q = attempt["question"]
                assert set(q) == {"id", "stem", "options"}
                assert set(q["options"]) == set("ABCDE") and q["id"] not in ids
                ids.add(q["id"])
                item = (
                    conn.execute(select(questions).where(questions.c.id == q["id"]))
                    .mappings()
                    .one()
                )
                subject = item["subtest_id"]
                assert item["difficulty"] == levels[subject]
                asked[subject] += 1
                # Mix responses on the full test and leave the retake blank.
                choice = (
                    (
                        item["correct_option"]
                        if step % 3 == 0
                        else next(x for x in "ABCDE" if x != item["correct_option"])
                        if step % 3 == 1
                        else None
                    )
                    if kind == "full"
                    else None
                )
                right = choice == item["correct_option"] if choice else None
                if choice:
                    answered[subject] += 1
                if right:
                    correct[subject] += 1
                levels[subject] = next_level(levels[subject], right)
                body = {
                    "client_answer_id": str(uuid4()),
                    "question_id": q["id"],
                    "selected_option": choice,
                    "not_sure": step % 2 == 0,
                }
                if step == 0:
                    assert client.post(post, headers=stranger, json=body).status_code == 404
                    with ThreadPoolExecutor(max_workers=2) as pool:
                        first, second = pool.map(
                            lambda _, url=post, payload=body: client.post(
                                url, headers=auth, json=payload
                            ),
                            range(2),
                        )
                    assert first.status_code == second.status_code == 200
                    assert first.json() == second.json()
                    response = first
                    assert (
                        client.post(
                            post,
                            headers=auth,
                            json={**body, "not_sure": not body["not_sure"]},
                        ).status_code
                        == 409
                    )
                else:
                    response = client.post(post, headers=auth, json=body)
                    response.raise_for_status()
                attempt = response.json()
                if step == 7:
                    assert start(kind) == attempt
            assert attempt["state"] == "completed" and attempt["question"] is None
            assert client.post(post, headers=auth, json=body).json() == attempt
            assert asked == Counter(sequence(kind))
            result = client.get(result_url, headers=auth).json()
            rows = result["subtests"]
            assert len(rows) == 6 and [r["priority"] for r in rows] == [
                True,
                True,
                False,
                False,
                False,
                False,
            ]
            assert [r["correct"] / r["asked"] for r in rows] == sorted(
                r["correct"] / r["asked"] for r in rows
            )
            for r in rows:
                assert (r["correct"], r["asked"]) == (
                    correct[r["subtest_id"]],
                    asked[r["subtest_id"]],
                )
            expected = estimate(
                {
                    "education": 30,
                    "verbal": 15,
                    "quantitative": 15,
                    "legislation": 8,
                    "history": 6,
                    "geography": 6,
                },
                correct,
                answered,
            )
            assert (result["net_low"], result["net_high"]) == expected
            preview = result["first_week"]
            assert (
                preview["daily_minutes"] == 60
                and len(preview["topics"]) == 3
                and preview["mock_day"] == "sunday"
            )
            assert client.get("/v1/plan/first-week", headers=auth).json() == preview
            assert (
                client.get("/v1/me", headers=auth).json()["placement"]["latest_id"]
                == attempt_id
            )
            assert (
                conn.scalar(
                    select(func.count())
                    .select_from(answers)
                    .where(answers.c.placement_id == attempt_id)
                )
                == total
            )


@pytest.mark.parametrize("change", [{"status": "quarantined"}, {"difficulty": 1}])
def test_plc_4_ineligible_question_replaced_without_counting_answer(
    demo: Settings, engine: Engine, change: dict[str, Any]
) -> None:
    with TestClient(create_app(demo)) as client:
        auth = guest(client)
        client.patch("/v1/me/profile", headers=auth, json=PROFILE).raise_for_status()
        state = client.post("/v1/placement", headers=auth, json={}).json()
        q = state["question"]["id"]
        with engine.begin() as conn:
            conn.execute(update(questions).where(questions.c.id == q).values(**change))
        body = {"client_answer_id": str(uuid4()), "question_id": q, "selected_option": None}
        assert (
            client.post(
                f"/v1/placement/{state['id']}/answers", headers=auth, json=body
            ).status_code
            == 409
        )
        resumed = client.post("/v1/placement", headers=auth, json={}).json()
        assert (
            resumed["id"] == state["id"]
            and resumed["position"] == 1
            and resumed["question"]["id"] != q
        )


def test_plc_4_retries_same_answer_after_missing_content_is_restored(
    demo: Settings, engine: Engine
) -> None:
    with TestClient(create_app(demo)) as client:
        auth = guest(client)
        client.patch("/v1/me/profile", headers=auth, json=PROFILE).raise_for_status()
        initial = client.post("/v1/placement", headers=auth, json={}).json()
        body = {
            "client_answer_id": str(uuid4()),
            "question_id": initial["question"]["id"],
            "selected_option": None,
        }
        url = f"/v1/placement/{initial['id']}/answers"
        with engine.begin() as conn:
            hidden = conn.scalars(
                update(questions)
                .where(
                    questions.c.subtest_id == "verbal",
                    questions.c.difficulty == 2,
                    questions.c.status == "published",
                )
                .values(status="quarantined")
                .returning(questions.c.id)
            ).all()
        assert client.post(url, headers=auth, json=body).status_code == 503
        assert client.post("/v1/placement", headers=auth, json={}).json() == initial
        with engine.begin() as conn:
            assert conn.scalar(select(func.count()).select_from(answers)) == 0
            conn.execute(
                update(questions)
                .where(questions.c.id.in_(hidden))
                .values(status="published")
            )
        assert client.post(url, headers=auth, json=body).json()["position"] == 2
