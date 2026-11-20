import asyncio
import base64
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from httpx import Response
from PIL import Image
from sqlalchemy import Engine, func, select
from study_support import grant_pass
from test_accounts import Inbox
from test_commerce import account
from test_practice import guest

from app.cli import delete_expired_photos
from app.core.db import Database
from app.core.http import ISTANBUL, ApiError, server_now
from app.core.settings import Settings
from app.main import create_app
from app.modules.accounts.email_login import email_sender
from app.modules.content.models import questions, remote_config
from app.modules.photos.models import solutions
from app.modules.photos.service import file_lock, purge
from app.modules.photos.solver import Reading, example, vision_solver
from app.modules.photos.storage import PhotoStore, normalize
from app.modules.photos.upload import MAX_BODY
from app.modules.practice.models import reports

PATH = "/v1/photo-solutions"
REPORT = "/v1/content-reports"


def test_upgrading_a_configured_m9_season_preserves_operator_values(
    catalogue_db: Settings,
    engine: Engine,
) -> None:
    migrations = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.downgrade(migrations, "0009_commerce")
    with engine.begin() as db:
        db.execute(
            remote_config.insert(),
            [
                {"key": "free_limits", "value": {"plan_days": 8}},
                {"key": "photo_retention_days", "value": 7},
            ],
        )
    command.upgrade(migrations, "head")
    with engine.connect() as db:
        values = dict(db.execute(select(remote_config)).tuples().all())
    assert values == {
        "free_limits": {"plan_days": 8},
        "photo_retention_days": 7,
        "photo_limits": {"free_total": 3, "pass_daily": 10},
        "photo_min_confidence": 0.75,
    }


def upload_data() -> dict[str, str]:
    out = BytesIO()
    exif = Image.Exif()
    exif[315] = "private camera owner"
    Image.new("RGB", (16, 12), "white").save(out, format="JPEG", exif=exif)
    return {"request_id": str(uuid4()), "image": base64.b64encode(out.getvalue()).decode()}


@pytest.mark.parametrize("format", ["PNG", "WEBP"])
def test_transparent_pages_remain_legible_after_conversion(format: str) -> None:
    out = BytesIO()
    page = Image.new("RGBA", (40, 20), (0, 0, 0, 0))
    page.paste((0, 0, 0, 255), (12, 6, 28, 14))
    page.save(out, format=format)
    jpeg = normalize(base64.b64encode(out.getvalue()).decode())
    with Image.open(BytesIO(jpeg)) as stored:
        assert stored.format == "JPEG"
        assert stored.getpixel((0, 0)) == (255, 255, 255)
        assert stored.getpixel((20, 10)) == (0, 0, 0)


def test_rejects_excessive_dimensions_and_multiframe_images() -> None:
    out = BytesIO()
    Image.new("1", (8000, 4001)).save(out, format="PNG")
    with pytest.raises(ApiError) as large:
        normalize(base64.b64encode(out.getvalue()).decode())
    assert large.value.status == 422
    out = BytesIO()
    Image.new("RGB", (2, 2), "white").save(
        out, format="PNG", save_all=True, append_images=[Image.new("RGB", (2, 2))]
    )
    with pytest.raises(ApiError) as animated:
        normalize(base64.b64encode(out.getvalue()).decode())
    assert animated.value.status == 422


class Recorder:
    def __init__(self, **changes: object) -> None:
        self.reading = example().model_copy(update=changes)
        self.images: list[bytes] = []

    async def solve(self, image: bytes) -> Reading:
        self.images.append(image)
        return self.reading


def config(engine: Engine, key: str, value: object) -> None:
    with engine.begin() as db:
        db.execute(
            remote_config.update().where(remote_config.c.key == key).values(value=value)
        )


def quota(c: TestClient, auth: dict[str, str]) -> dict[str, Any]:
    r = c.get(PATH + "/quota", headers=auth)
    r.raise_for_status()
    return dict(r.json())


def test_private_submission_report_and_unchanged_bank(
    seeded: Settings, engine: Engine
) -> None:
    app = create_app(seeded)
    solver = Recorder()
    app.dependency_overrides[vision_solver] = lambda: solver
    with TestClient(app) as c, engine.connect() as db:
        before = db.execute(select(questions).order_by(questions.c.id)).all()
        owner, other = guest(c), guest(c)
        data = upload_data()
        assert c.post(PATH, json=data).status_code == 401
        assert c.get(PATH + "/quota").status_code == 401
        res = c.post(PATH, headers=owner, json=data)
        res.raise_for_status()
        assert "no-store" in res.headers["cache-control"]
        body = res.json()
        id = body["id"]
        result = body["result"]
        assert result["is_placeholder"] and result["state"] == "solved"
        assert result["question"] and result["answer"] and len(result["steps"]) == 2
        assert c.get("/v1/lessons/" + result["lesson"]["id"], headers=owner).is_success
        assert c.get(f"{PATH}/{id}", headers=owner).json() == body
        assert c.post(PATH, headers=owner, json=data).json() == body
        assert len(solver.images) == 1
        raw = PhotoStore(seeded.photo_storage_dir).path(UUID(id)).read_bytes()
        assert raw == solver.images[0] and b"private camera owner" not in raw
        assert not Image.open(BytesIO(raw)).getexif()
        assert Image.open(BytesIO(base64.b64decode(body["preview_jpeg"]))).format == "JPEG"
        assert c.get(f"{PATH}/{id}", headers=other).status_code == 404
        assert c.get(f"{PATH}/{id}").status_code == 401
        report = {"photo_solution_id": id, "text": "Örnek bildirim"}
        assert c.post(REPORT, headers=other, json=report).status_code == 404
        assert (
            c.post(REPORT, headers=owner, json={**report, "text": " "}).status_code == 422
        )
        assert (
            c.post(REPORT, headers=owner, json={**report, "question_id": "x"}).status_code
            == 422
        )
        for _ in range(2):
            assert c.post(REPORT, headers=owner, json=report).json() == {"received": True}
        assert db.scalar(select(func.count()).select_from(reports)) == 1
        saved = db.execute(select(solutions)).one()
        assert "preview" not in str(saved.result) and data["image"] not in str(saved.result)
        assert db.execute(select(questions).order_by(questions.c.id)).all() == before
        assert quota(c, owner) == {"remaining": 2, "period": "lifetime"}
        assert quota(c, other)["remaining"] == 3


@pytest.mark.parametrize(
    ("changes", "state"),
    [
        ({"confidence": 0.79}, "low_confidence"),
        ({"confidence": 0.8}, "solved"),
        ({"in_scope": False}, "out_of_scope"),
        ({"topic_id": "unknown"}, "out_of_scope"),
    ],
)
def test_server_refusals_hide_provider_content(
    seeded: Settings,
    engine: Engine,
    changes: dict[str, object],
    state: str,
) -> None:
    config(engine, "photo_min_confidence", 0.8)
    solver = Recorder(**changes)
    app = create_app(seeded)
    app.dependency_overrides[vision_solver] = lambda: solver
    with TestClient(app) as c:
        owner = guest(c)
        response = c.post(PATH, headers=owner, json=upload_data())
        response.raise_for_status()
        result = response.json()["result"]
        assert result["state"] == state
        if state != "solved":
            assert not result["steps"] and not result["answer"] and not result["question"]
        if state == "out_of_scope":
            assert not result["topic"] and not result["lesson"]
        else:
            assert result["topic"] and result["lesson"]
        assert quota(c, owner)["remaining"] == 2


@pytest.mark.parametrize("paid", [False, True])
def test_concurrent_quota_retry_and_istanbul_midnight(
    seeded: Settings,
    engine: Engine,
    paid: bool,
) -> None:
    app = create_app(seeded)
    now = datetime(2027, 2, 1, 23, 59, tzinfo=ISTANBUL)
    with TestClient(app) as c:
        owner = guest(c)
        if paid:
            grant_pass(c, owner, engine, now.date() + timedelta(days=2))
        app.dependency_overrides[server_now] = lambda: now
        initial = 10 if paid else 3
        assert quota(c, owner)["remaining"] == initial

        def send(data: dict[str, str]) -> Response:
            return c.post(PATH, headers=owner, json=data)

        first = upload_data()
        with ThreadPoolExecutor(2) as pool:
            a, b = list(pool.map(send, [first, first]))
            assert a.is_success and a.json() == b.json()
            for _ in range(initial - 2):
                send(upload_data()).raise_for_status()
            boundary = list(pool.map(send, [upload_data(), upload_data()]))
        assert sorted(r.status_code for r in boundary) == [200, 403]
        code = "daily_limit_reached" if paid else "free_limit_reached"
        assert next(r for r in boundary if r.status_code == 403).json()["code"] == code
        assert send(first).json() == a.json()
        assert quota(c, owner)["remaining"] == 0
        now += timedelta(minutes=1)
        assert quota(c, owner)["remaining"] == (10 if paid else 0)
        config(engine, "photo_limits", {"free_total": 5, "pass_daily": 11})
        assert quota(c, owner)["remaining"] == (11 if paid else 2)
        assert c.get("/v1/paywall?platform=web", headers=owner).json()["photo_limits"] == {
            "free_total": 5,
            "pass_daily": 11,
        }


def test_invalid_photo_storage_failure_and_disabled_provider_use_no_allowance(
    seeded: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = create_app(seeded)
    with TestClient(app) as c:
        owner = guest(c)
        data = upload_data()
        for invalid in ["not!base64", base64.b64encode(b"<svg/>").decode()]:
            assert (
                c.post(PATH, headers=owner, json={**data, "image": invalid}).status_code
                == 422
            )
        for body in (b"x" * (MAX_BODY + 1), iter([b"x" * (MAX_BODY + 1)])):
            res = c.post(
                PATH, headers={**owner, "content-type": "application/json"}, content=body
            )
            assert res.status_code == 413 and res.json()["code"] == "invalid_photo"
        seeded.app_env = "production"
        assert c.post(PATH, headers=owner, json=data).status_code == 503
        seeded.app_env = "development"

        def fail(self: PhotoStore, id: UUID, jpeg: bytes) -> None:
            raise OSError("storage full")

        with monkeypatch.context() as m:
            m.setattr(PhotoStore, "save", fail)
            assert c.post(PATH, headers=owner, json=data).status_code == 503
        assert quota(c, owner)["remaining"] == 3
        c.post(PATH, headers=owner, json=data).raise_for_status()


def test_retention_job_deadline_orphans_and_retry(seeded: Settings, engine: Engine) -> None:
    now = server_now()
    app = create_app(seeded)
    store = PhotoStore(seeded.photo_storage_dir)
    with TestClient(app) as c:
        owner = guest(c)
        app.dependency_overrides[server_now] = lambda: now
        id = UUID(c.post(PATH, headers=owner, json=upload_data()).json()["id"])
        c.post(
            REPORT, headers=owner, json={"photo_solution_id": str(id), "text": "Örnek"}
        ).raise_for_status()
        now += timedelta(days=30) - timedelta(seconds=1)
        assert c.get(f"{PATH}/{id}", headers=owner).is_success
        orphan = uuid4()
        store.save(orphan, b"interrupted write")

        async def sweep() -> int:
            database = Database(seeded.database_url)
            try:
                async with database.sessions() as db:
                    return await purge(db, store, now)
            finally:
                await database.engine.dispose()

        with engine.begin() as writer:
            writer.execute(select(func.pg_advisory_xact_lock(file_lock(orphan))))
            assert asyncio.run(sweep()) == 0
        assert asyncio.run(sweep()) == 1
        assert store.path(id).exists() and not store.path(orphan).exists()
        now += timedelta(seconds=1)
        assert c.get(f"{PATH}/{id}", headers=owner).status_code == 404
        assert (
            c.post(
                REPORT, headers=owner, json={"photo_solution_id": str(id), "text": "Örnek"}
            ).status_code
            == 404
        )
        assert asyncio.run(sweep()) == 1 and not store.path(id).exists()
        assert asyncio.run(sweep()) == 0
        with engine.connect() as db:
            assert not db.scalar(select(func.count()).select_from(reports))
            assert not db.scalar(select(func.count()).select_from(solutions))
        assert quota(c, owner)["remaining"] == 2
        config(engine, "photo_retention_days", 1)
        past = server_now() - timedelta(days=2)
        app.dependency_overrides[server_now] = lambda: past
        c.post(PATH, headers=owner, json=upload_data()).raise_for_status()
        assert asyncio.run(delete_expired_photos(seeded)) == 1


def test_guest_merge_preserves_private_results_and_account_erase_removes_files(
    seeded: Settings, engine: Engine
) -> None:
    app, inbox = create_app(seeded), Inbox()
    app.dependency_overrides[email_sender] = lambda: inbox
    with TestClient(app) as c:
        target = account(c, inbox, guest(c), "photo@example.com")
        source = guest(c)
        same_key = upload_data()
        ids = [
            c.post(PATH, headers=user, json=same_key).json()["id"]
            for user in (target, source)
        ]
        c.post(
            REPORT, headers=source, json={"photo_solution_id": ids[1], "text": "Örnek"}
        ).raise_for_status()
        final = account(c, inbox, source, "photo@example.com")
        assert quota(c, final)["remaining"] == 1
        assert c.get(f"{PATH}/{ids[1]}", headers=source).status_code == 401
        for id in ids:
            assert c.get(f"{PATH}/{id}", headers=final).is_success
        with engine.connect() as db:
            assert db.scalar(select(func.count()).select_from(reports)) == 1
        c.delete("/v1/me", headers=final).raise_for_status()
        assert not PhotoStore(seeded.photo_storage_dir).ids()
        with engine.connect() as db:
            assert not db.scalar(select(func.count()).select_from(solutions))
            assert not db.scalar(select(func.count()).select_from(reports))
