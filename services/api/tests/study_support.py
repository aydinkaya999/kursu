from datetime import date
from typing import Any
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import Engine

from app.modules.notebook.models import entitlements


def grant_pass(c: TestClient, auth: dict[str, str], engine: Engine, until: date) -> None:
    user = UUID(c.get("/v1/me", headers=auth).json()["id"])
    with engine.begin() as db:
        db.execute(
            entitlements.insert().values(
                user_id=user, kind="season_pass", source="web", valid_until=until
            )
        )


def practice_start(
    c: TestClient, auth: dict[str, str], kind: str, content_id: str, task: str | None = None
) -> dict[str, Any]:
    r = c.post(
        "/v1/practice-sessions",
        headers=auth,
        json={"kind": kind, "content_id": content_id, "task_id": task},
    )
    r.raise_for_status()
    return dict(r.json())


def finish_task(c: TestClient, auth: dict[str, str], task: dict[str, Any]) -> None:
    path = "/v1/plan/tasks/" + task["id"]
    c.post(path + "/start", headers=auth).raise_for_status()
    if task["state"] != "done" and task["kind"] in ("lesson", "topic_test"):
        kind = "lesson_check" if task["kind"] == "lesson" else "topic_test"
        state = practice_start(c, auth, kind, task["content_id"], task["id"])
        url = "/v1/practice-sessions/" + state["id"]
        while state["state"] == "question":
            response = c.post(
                url + "/answers",
                headers=auth,
                json={
                    "client_answer_id": str(uuid4()),
                    "question_id": state["question"]["id"],
                    "selected_option": None,
                },
            )
            response.raise_for_status()
            state = response.json()
        c.post(url + "/finish", headers=auth).raise_for_status()
    if task["state"] != "done" and task["kind"] == "mock":
        result = c.post(
            "/v1/mocks/" + task["content_id"] + "/attempts",
            headers=auth,
            json={"mode": "timed"},
        )
        result.raise_for_status()
        c.post(
            "/v1/mock-attempts/" + result.json()["id"] + "/submit", headers=auth
        ).raise_for_status()
    c.post(path + "/complete", headers=auth).raise_for_status()
