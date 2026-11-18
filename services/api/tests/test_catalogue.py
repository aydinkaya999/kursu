from fastapi.testclient import TestClient
from sqlalchemy import Engine, Table, select, update

from app.core.settings import Settings
from app.main import create_app
from app.modules.content import models as db
from app.modules.content.bundle import Bundle


def test_subtests_match_exam_section_3_and_fields_match_onboarding(
    seeded: Settings,
) -> None:
    with TestClient(create_app(seeded)) as client:
        subtests = client.get("/v1/subtests")
        fields = client.get("/v1/fields")
    assert subtests.status_code == fields.status_code == 200
    start = 1
    ordered = []
    for row in subtests.json():
        end = start + row["question_count"] - 1
        ordered.append(
            (
                row["id"],
                row["name"],
                row["short_name"],
                row["exam_order"],
                row["weight_p1"],
                start,
                end,
            )
        )
        start = end + 1
    assert ordered == [
        ("verbal", "Sözel Yetenek", "Sözel", 1, 20, 1, 15),
        ("quantitative", "Sayısal Yetenek", "Sayısal", 2, 20, 16, 30),
        ("history", "Tarih", "Tarih", 3, 15, 31, 36),
        ("geography", "Türkiye Coğrafyası", "Coğrafya", 4, 10, 37, 42),
        ("education", "Eğitim Bilimleri", "Eğitim Bilimleri", 5, 25, 43, 72),
        ("legislation", "Mevzuat", "Mevzuat", 6, 10, 73, 80),
    ]
    assert {f["name"]: f["score_type"] for f in fields.json()} == {
        "Sınıf Öğretmenliği": "P2",
        "Okul Öncesi Öğretmenliği": "P2",
        "Türkçe Öğretmenliği": "P2",
        "İngilizce Öğretmenliği": "P3",
    }


def test_topics_and_lessons_can_be_filtered(seeded: Settings, sample: Bundle) -> None:
    with TestClient(create_app(seeded)) as client:
        assert len(client.get("/v1/topics").json()) == len(sample["topics"])
        response = client.get("/v1/topics", params={"subtest_id": "quantitative"})
        assert response.status_code == 200
        assert {t["id"] for t in response.json()} == {
            "quantitative.percent-ratio",
            "quantitative.work-problems",
        }
        assert all(t["exam_weight"] is None for t in response.json())
        lesson = sample["lessons"][0]
        response = client.get("/v1/lessons", params={"topic_id": lesson["topic_id"]})
        assert response.status_code == 200
        assert response.json() == [
            {
                "id": lesson["id"],
                "title": lesson["title"],
                "topic_id": lesson["topic_id"],
                "minutes": 5,
                "is_placeholder": False,
            }
        ]
        assert client.get("/v1/lessons", params={"topic_id": "unknown"}).json() == []


def test_why_6_check_questions_expose_only_unanswered_fields(
    seeded: Settings, sample: Bundle
) -> None:
    lesson = sample["lessons"][0]
    with TestClient(create_app(seeded)) as client:
        response = client.get(f"/v1/lessons/{lesson['id']}")
    assert response.status_code == 200
    detail = response.json()
    assert detail["title"] == lesson["title"]
    assert detail["source"] == lesson["source"]
    assert detail["cards"] == [
        {"tip": None, **card, "position": i} for i, card in enumerate(lesson["cards"], 1)
    ]
    questions = {q["id"]: q for q in sample["questions"]}
    assert detail["check_questions"] == [
        {key: questions[check["question_id"]][key] for key in ("id", "stem", "options")}
        for check in lesson["check_questions"]
    ]


def test_cnt_1_hidden_items_and_their_questions_are_unavailable(
    demo: Settings, engine: Engine
) -> None:
    mock = "mock.example.01"
    with engine.connect() as conn:
        slots = db.mock_exam_questions.c
        question = conn.execute(
            select(slots.question_id).where(slots.mock_exam_id == mock, slots.position == 1)
        ).scalar_one()
        checks = db.lesson_check_questions.c
        lesson = conn.execute(
            select(checks.lesson_id).where(checks.question_id == question)
        ).scalar_one()

    def set_status(table: Table, key: str, status: str) -> None:
        with engine.begin() as conn:
            conn.execute(update(table).where(table.c.id == key).values(status=status))

    with TestClient(create_app(demo)) as client:
        unknown = client.get("/v1/lessons/unknown")
        assert unknown.status_code == 404
        assert unknown.json()["code"] == "not_found"

        def check_visibility(visible: bool) -> None:
            lessons, mocks = client.get("/v1/lessons"), client.get("/v1/mocks")
            assert lessons.status_code == mocks.status_code == 200
            assert (lesson in [item["id"] for item in lessons.json()]) == visible
            assert (mock in [item["id"] for item in mocks.json()]) == visible
            assert set(mocks.json()[0]) == {"id", "title", "published_at", "is_placeholder"}
            detail = client.get(f"/v1/lessons/{lesson}")
            if visible:
                assert detail.status_code == 200
            else:
                assert detail.status_code == 404
                assert detail.json() == unknown.json()

        check_visibility(True)
        for status in ("draft", "prerelease", "quarantined", "retired"):
            set_status(db.lessons, lesson, status)
            set_status(db.mock_exams, mock, status)
            check_visibility(False)
            set_status(db.lessons, lesson, "published")
            set_status(db.mock_exams, mock, "published")
            set_status(db.questions, question, status)
            check_visibility(False)
            set_status(db.questions, question, "published")
        check_visibility(True)
