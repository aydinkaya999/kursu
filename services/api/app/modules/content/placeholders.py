"""Build deterministic, visibly artificial development data from the seed taxonomy."""

from collections import defaultdict

from app.modules.content.bundle import MARKER, Bundle, Row

# Development coverage for the 31-topic map. The official topic names come from imports.
DEMO_TOPIC_COUNTS = {
    "verbal": 6,
    "quantitative": 6,
    "history": 2,
    "geography": 2,
    "education": 12,
    "legislation": 3,
}
CARD_HEADINGS = {
    "definition": "Tanım",
    "example": "Örnek",
    "confused": "Karşılaştırma",
    "exam": "Alıştırma",
}


def make_lesson(topic: Row, question_ids: list[str]) -> Row:
    title = f"{MARKER} Mikro ders · {topic['name'].removeprefix(MARKER).strip()}"
    return {
        "id": f"lesson.example.{topic['id']}",
        "topic_id": topic["id"],
        "title": title,
        "minutes": 4,
        "status": "published",
        "is_placeholder": True,
        "source": {
            "kind": "notes",
            "title": f"{MARKER} Geliştirme notları",
            "section": topic["name"],
        },
        "cards": [
            {
                "kind": kind,
                "title": heading,
                "blocks": [{"heading": heading, "text": f"{title} · {heading} kartı."}],
            }
            for kind, heading in CARD_HEADINGS.items()
        ],
        "check_questions": [
            {"question_id": question_ids[0], "card_position": 1},
            {"question_id": question_ids[1], "card_position": 2},
        ],
    }


def make_question(
    topic: Row, objective: str, misconception: str, level: int, number: int
) -> Row:
    subject = topic["subtest_id"]
    name = topic["name"].removeprefix(MARKER).strip()
    initial = level * 10
    total = initial + number
    labels = "ABCDE"
    answer_index = (level + number) % len(labels)
    options = {letter: str(total + i - answer_index) for i, letter in enumerate(labels)}
    rationales = {
        letter: {
            "text": f"{MARKER} Kartları yeniden say.",
            "misconception_id": misconception,
        }
        for letter in labels
    }
    rationales[labels[answer_index]] = {"text": f"{MARKER} Toplam {total} kart vardır."}
    source: Row = {"kind": "lesson", "lesson_title": f"{MARKER} Mikro ders · {name}"}
    if subject == "legislation":
        source = {
            "kind": "law",
            "short_name": f"{MARKER} Kurgusal metin",
            "article": 1,
            "quote": f"{MARKER} Yalnızca geliştirme için örnek madde.",
        }
    return {
        "id": f"q.example.{topic['id']}.{level}.{number:02}",
        "topic_id": topic["id"],
        "subtest_id": subject,
        "objective_id": objective,
        "difficulty": level,
        "status": "published",
        "is_placeholder": True,
        "stem": f"{MARKER} {name} · {initial} karta {number} kart eklenirse kaç kart olur?",
        "options": options,
        "correct_option": labels[answer_index],
        "rationales": rationales,
        "solution_steps": [{"title": "Topla", "text": f"{initial} + {number} = {total}"}],
        "source": source,
        "related_lesson_id": f"lesson.example.{topic['id']}",
    }


def make_placeholders(seed: Bundle) -> Bundle:
    result: Bundle = {
        "schema_version": 1,
        "topics": [],
        "objectives": [],
        "misconceptions": [],
        "questions": [],
        "lessons": [],
        "mock_exams": [],
    }
    sections = sorted(seed["subtests"], key=lambda s: s["exam_order"])
    topics = list(seed["topics"])
    objectives = {obj["topic_id"]: obj["id"] for obj in seed["objectives"]}
    bank: dict[str, list[str]] = defaultdict(list)
    for section in sections:
        subject = section["id"]
        supplied = sum(topic["subtest_id"] == subject for topic in topics)
        for number in range(1, DEMO_TOPIC_COUNTS[subject] - supplied + 1):
            topic = {
                "id": f"{subject}.example-{number:02}",
                "subtest_id": subject,
                "name": f"{MARKER} {section['short_name']} · Konu {number}",
                "is_placeholder": True,
            }
            topics.append(topic)
            result["topics"].append(topic)

    for topic in topics:
        topic_id = topic["id"]
        objective = objectives.get(topic_id)
        if objective is None:
            objective = f"obj.example.{topic_id}"
            result["objectives"].append(
                {
                    "id": objective,
                    "topic_id": topic_id,
                    "text": f"{MARKER} Kart sayısını belirler.",
                    "is_placeholder": True,
                }
            )
        misconception = f"mis.example.{topic_id}"
        result["misconceptions"].append(
            {
                "id": misconception,
                "topic_id": topic_id,
                "text": f"{MARKER} Kart sayısını karıştırmak",
                "is_placeholder": True,
            }
        )
        questions = [
            make_question(topic, objective, misconception, level, number)
            for level in range(1, 4)
            for number in range(1, 11)
        ]
        ids = [q["id"] for q in questions]
        bank[topic["subtest_id"]].extend(ids)
        result["questions"].extend(questions)
        result["lessons"].append(make_lesson(topic, ids))

    for index in range(10):
        ids = []
        for section in sections:
            count = section["question_count"]
            ids.extend(bank[section["id"]][index * count : (index + 1) * count])
        result["mock_exams"].append(
            {
                "id": f"mock.example.{index + 1:02}",
                "title": f"{MARKER} Deneme {index + 1}",
                "status": "published",
                "published_at": "2026-11-18T00:00:00Z",
                "is_placeholder": True,
                "question_ids": ids,
            }
        )
    return result
