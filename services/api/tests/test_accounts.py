from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import Engine, func, select, update
from study_support import finish_task, practice_start

from app.core.settings import Settings
from app.main import create_app
from app.modules.accounts.email_login import SMTPSender, email_sender
from app.modules.accounts.models import (
    email_codes,
    identities,
    profiles,
    refresh_tokens,
    users,
)
from app.modules.accounts.providers import IdentityProvider, Provider, provider_client
from app.modules.placement.models import answers, attempts
from app.modules.plan.models import plans, streaks, tasks
from app.modules.practice.models import completions, mastery, reports, sessions


class Inbox:
    def __init__(self) -> None:
        self.codes: dict[str, str] = {}

    def send(self, email: str, code: str) -> None:
        self.codes[email] = code


def test_smtp_renders_the_packaged_template_with_the_code() -> None:
    settings = Settings(smtp_host="mail.example.org", email_sender="sender@example.org")
    with patch("smtplib.SMTP", autospec=True) as connect:
        SMTPSender(settings).send("candidate@example.org", "012345")
    mail = connect.return_value.__enter__.return_value
    mail.starttls.assert_called_once()
    message = mail.send_message.call_args.args[0]
    assert (
        message["From"] == "sender@example.org" and message["To"] == "candidate@example.org"
    )
    assert message["Subject"] and "012345" in message.get_content()


class TestIssuer(IdentityProvider):
    __test__ = False

    def __init__(self, provider: Provider, cfg: Settings) -> None:
        super().__init__(provider, cfg)
        self.audiences = ["test-client"]
        self.secret = "only-in-test"
        self.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.codes: dict[str, str] = {}

    def token(self, nonce: str, subject: str = "subject-17", **overrides: Any) -> str:
        now = datetime.now(UTC)
        claims = {
            "iss": self.endpoints.issuers[0],
            "aud": self.audiences[0],
            "iat": now,
            "exp": now + timedelta(minutes=5),
            "sub": subject,
            "nonce": nonce,
            **overrides,
        }
        return jwt.encode(claims, self.key, algorithm="RS256")

    def exchange(self, code: str, verifier: str) -> str:
        return self.codes.pop(code)

    def signing_key(self, token: str) -> Any:
        return self.key.public_key()


@pytest.fixture
def auth_app(demo: Settings) -> Iterator[tuple[TestClient, Inbox, dict[str, TestIssuer]]]:
    app = create_app(demo)
    inbox = Inbox()
    ops = {p: TestIssuer(p, demo) for p in ("google", "apple")}

    def issuer(provider: Provider) -> TestIssuer:
        return ops[provider]

    app.dependency_overrides[provider_client] = issuer
    app.dependency_overrides[email_sender] = lambda: inbox
    with TestClient(app, base_url="https://testserver") as client:
        yield client, inbox, ops


type Harness = tuple[TestClient, Inbox, dict[str, TestIssuer]]


def headers(tokens: dict[str, Any]) -> dict[str, str]:
    return {"Authorization": "Bearer " + tokens["access_token"]}


def new_guest(client: TestClient, complete: bool = False) -> tuple[dict[str, str], str]:
    auth = headers(client.post("/v1/auth/guest", json={"platform": "native"}).json())
    client.patch(
        "/v1/me/profile",
        headers=auth,
        json={
            "field_id": "sinif-ogretmenligi",
            "daily_minutes": 60,
            "attempt_kind": "first",
        },
    ).raise_for_status()
    attempt = client.post("/v1/placement", headers=auth, json={}).json()
    for _ in range(30 if complete else 1):
        reply = client.post(
            f"/v1/placement/{attempt['id']}/answers",
            headers=auth,
            json={
                "client_answer_id": str(uuid4()),
                "question_id": attempt["question"]["id"],
                "selected_option": None,
            },
        )
        reply.raise_for_status()
        attempt = reply.json()
    return auth, attempt["id"]


def login(h: Harness, auth: dict[str, str], method: str) -> dict[str, Any]:
    client, inbox, ops = h
    if method == "email":
        email = "candidate@example.org"
        client.post(
            "/v1/auth/email/start", headers=auth, json={"email": email}
        ).raise_for_status()
        response = client.post(
            "/v1/auth/email/verify",
            headers=auth,
            json={"email": email, "code": inbox.codes[email], "platform": "native"},
        )
    else:
        result = client.post(
            f"/v1/auth/{method}/start", headers=auth, json={"platform": "native"}
        )
        result.raise_for_status()
        challenge = result.json()
        op = ops[method]
        op.codes["provider-code"] = op.token(challenge["nonce"])
        data = {"state": challenge["state"], "code": "provider-code"}
        url = "/v1/auth/callback/" + method
        redirect = (
            client.get(url, params=data, follow_redirects=False)
            if method == "google"
            else client.post(url, data=data, follow_redirects=False)
        )
        assert redirect.status_code == 303 and redirect.headers["location"].startswith(
            "kursu://auth?"
        )
        finish = {
            "state": parse_qs(urlsplit(redirect.headers["location"]).query)["state"][0],
            "platform": "native",
        }
        response = client.post("/v1/auth/" + method, headers=auth, json=finish)
    response.raise_for_status()
    return dict(response.json())


@pytest.mark.parametrize("method", ["email", "google", "apple"])
def test_onb_5_onb_6_signup_merge_delete_and_refresh(
    auth_app: Harness, engine: Engine, method: str
) -> None:
    client, _, _ = auth_app
    guest, first = new_guest(client, True)
    before = client.get("/v1/me", headers=guest).json()
    tokens = login(auth_app, guest, method)
    account = headers(tokens)
    me = client.get("/v1/me", headers=account).json()
    assert (
        me["id"] == before["id"]
        and not me["is_guest"]
        and before["profile"] == me["profile"]
    )
    assert client.get("/v1/me", headers=guest).status_code == 401
    result = client.get(f"/v1/placement/{first}/result", headers=account).json()
    assert result["total"] == 30
    day = client.get("/v1/plan/today", headers=account).json()
    assert day["net_range"] == {"low": result["net_low"], "high": result["net_high"]}
    assert len(day["priorities"]) == 3 and day["net_change"] is None
    second, attempt = new_guest(client)
    second_id = client.get("/v1/me", headers=second).json()["id"]
    tokens2 = login(auth_app, second, method)
    merged = headers(tokens2)
    merged_me = client.get("/v1/me", headers=merged).json()
    assert merged_me["id"] == me["id"] and merged_me["placement"]["active_id"] == attempt
    assert client.get("/v1/me", headers=second).status_code == 401
    with engine.connect() as db:
        assert db.scalar(select(func.count()).select_from(answers)) == 31
        assert db.scalar(select(func.count()).select_from(attempts)) == 2
        assert db.scalar(select(users.c.id).where(users.c.id == second_id)) is None
        assert db.scalar(select(func.count()).select_from(identities)) == 1
    refresh = {"platform": "native", "refresh_token": tokens2["refresh_token"]}
    rotated = client.post("/v1/auth/refresh", json=refresh)
    rotated.raise_for_status()
    assert client.post("/v1/auth/refresh", json=refresh).status_code == 401
    auth = headers(rotated.json())
    assert client.patch(
        "/v1/me/settings",
        headers=auth,
        json={"daily_minutes": 90, "notification_time": "19:30"},
    ).json() == {"daily_minutes": 90, "notification_time": "19:30:00"}
    assert client.get("/v1/me/settings", headers=auth).json()["daily_minutes"] == 90
    assert (
        client.patch(
            "/v1/me/settings", headers=auth, json={"daily_minutes": 45}
        ).status_code
        == 422
    )
    assert client.post("/v1/auth/logout", headers=auth).status_code == 200
    assert client.get("/v1/me", headers=auth).status_code == 401
    assert client.get("/v1/me", headers=account).status_code == 200
    deleted = client.delete("/v1/me", headers=account)
    assert (
        deleted.status_code == 200 and "max-age=0" in deleted.headers["set-cookie"].lower()
    )
    assert client.get("/v1/me", headers=account).status_code == 401
    with engine.connect() as db:
        for table in (
            users,
            profiles,
            identities,
            email_codes,
            refresh_tokens,
            attempts,
            answers,
        ):
            assert db.scalar(select(func.count()).select_from(table)) == 0


def test_codes_attempts_expiration_and_provider_claims(
    auth_app: Harness, engine: Engine
) -> None:
    client, inbox, ops = auth_app
    guest, _ = new_guest(client)
    email = "test@example.org"
    assert (
        client.post(
            "/v1/auth/email/start", headers=guest, json={"email": email}
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/v1/auth/email/start", headers=guest, json={"email": email}
        ).status_code
        == 429
    )
    valid = inbox.codes[email]

    def verify(code: str) -> int:
        return client.post(
            "/v1/auth/email/verify",
            headers=guest,
            json={"platform": "native", "email": email, "code": code},
        ).status_code

    for _ in range(5):
        assert verify("000000" if valid != "000000" else "999999") == 400
    assert verify(valid) == 400
    with engine.begin() as db:
        db.execute(
            update(email_codes).values(
                attempts=0, expires_at=datetime.now(UTC) - timedelta(seconds=1)
            )
        )
    assert verify(valid) == 400
    c = client.post(
        "/v1/auth/google/start", headers=guest, json={"platform": "native"}
    ).json()
    op = ops["google"]
    for kv in (
        {"aud": "other"},
        {"iss": "other"},
        {"exp": 1},
        {"nonce": "wrong"},
        {"azp": "other"},
    ):
        token = op.token(**{"nonce": c["nonce"], **kv})
        assert (
            client.post(
                "/v1/auth/google",
                headers=guest,
                json={"platform": "native", "state": c["state"], "id_token": token},
            ).status_code
            == 400
        )
    token = op.token(c["nonce"])
    data = {"platform": "native", "state": c["state"], "id_token": token}
    outsider, _ = new_guest(client)
    assert client.post("/v1/auth/google", headers=outsider, json=data).status_code == 400
    assert client.post("/v1/auth/google", headers=guest, json=data).status_code == 200
    assert client.post("/v1/auth/google", headers=guest, json=data).status_code == 401


def test_two_unfinished_attempts_survive_merge(auth_app: Harness, engine: Engine) -> None:
    client, _, _ = auth_app
    first, a = new_guest(client)
    login(auth_app, first, "email")
    second, b = new_guest(client)
    auth = headers(login(auth_app, second, "email"))
    assert client.post("/v1/placement", headers=auth, json={}).json()["id"] == a
    with engine.begin() as db:
        assert db.scalar(select(attempts.c.state).where(attempts.c.id == b)) == "paused"
        db.execute(
            update(attempts)
            .where(attempts.c.id == a)
            .values(state="completed", completed_at=datetime.now(UTC))
        )
    resumed = client.post("/v1/placement", headers=auth, json={}).json()
    assert resumed["id"] == b and resumed["position"] == 2


def test_daily_history_merge_preserves_completed_days_without_duplicate_tasks(
    auth_app: Harness, engine: Engine
) -> None:
    client, _, _ = auth_app
    guest, _ = new_guest(client)
    # Keep the real-clock account journey within a study season on future CI runs.
    from app.core.http import ISTANBUL
    from app.modules.content.models import remote_config

    with engine.begin() as db:
        db.execute(
            update(remote_config)
            .where(remote_config.c.key == "exam_date")
            .values(value=(datetime.now(ISTANBUL).date() + timedelta(days=100)).isoformat())
        )
    first = client.get("/v1/plan/today", headers=guest).json()
    for task in first["tasks"]:
        finish_task(client, guest, task)
    account = headers(login(auth_app, guest, "email"))
    assert client.get("/v1/plan/today", headers=account).json()["streak"] == 1
    fresh, _ = new_guest(client)
    second = client.get("/v1/plan/today", headers=fresh).json()
    finish_task(client, fresh, second["tasks"][0])
    merged = headers(login(auth_app, fresh, "email"))
    day = client.get("/v1/plan/today", headers=merged).json()
    assert day["done"] == day["total"] == first["total"] and day["streak"] == 1
    assert [t["id"] for t in day["tasks"]] == [t["id"] for t in first["tasks"]]
    with engine.connect() as db:
        assert db.scalar(select(func.count()).select_from(plans)) == 1
        assert db.scalar(select(func.count()).select_from(tasks)) == first["total"]
    client.delete("/v1/me", headers=merged).raise_for_status()
    with engine.connect() as db:
        for table in (plans, tasks, streaks):
            assert db.scalar(select(func.count()).select_from(table)) == 0


def test_study_data_survives_account_merge_and_is_erased_on_deletion(
    auth_app: Harness, engine: Engine
) -> None:
    client, _, _ = auth_app
    lesson = "lesson.legislation.firsat-ve-imkan-esitligi"
    guest, _ = new_guest(client)
    first = headers(login(auth_app, guest, "email"))
    second, _ = new_guest(client)
    for user in (first, second):
        state = practice_start(client, user, "lesson_check", lesson)
        url = "/v1/practice-sessions/" + state["id"]
        for selected in ("B", "C"):
            question = state["question"]["id"]
            client.post(
                url + "/answers",
                headers=user,
                json={
                    "question_id": question,
                    "selected_option": selected,
                    "client_answer_id": str(uuid4()),
                },
            ).raise_for_status()
            state = client.post(
                url + "/advance", headers=user, json={"question_id": question}
            ).json()
        client.post(url + "/finish", headers=user).raise_for_status()
        client.post(
            "/v1/content-reports",
            headers=user,
            json={"question_id": question, "text": "Maddeyi kontrol edin."},
        ).raise_for_status()
    unfinished = practice_start(client, second, "topic_test", "quantitative.percent-ratio")
    merged = headers(login(auth_app, second, "email"))
    assert (
        client.get("/v1/practice-sessions/" + unfinished["id"], headers=merged).json()
        == unfinished
    )
    with engine.connect() as db:
        assert db.scalar(select(func.count()).select_from(completions)) == 1
        assert db.scalar(select(func.count()).select_from(reports)) == 1
        assert db.scalar(select(func.count()).select_from(sessions)) == 3
        assert (
            db.scalar(
                select(func.count())
                .select_from(answers)
                .where(answers.c.practice_id.is_not(None))
            )
            == 4
        )
        assert (
            db.scalar(
                select(mastery.c.answers_count).where(
                    mastery.c.topic_id == "legislation.law-1739-principles"
                )
            )
            == 4
        )
    client.delete("/v1/me", headers=merged).raise_for_status()
    with engine.connect() as db:
        for table in (sessions, answers, mastery, completions, reports):
            assert db.scalar(select(func.count()).select_from(table)) == 0
