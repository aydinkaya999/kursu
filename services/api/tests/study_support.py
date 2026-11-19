from typing import Any
from uuid import uuid4

from fastapi.testclient import TestClient


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
    c.post(path + "/complete", headers=auth).raise_for_status()
