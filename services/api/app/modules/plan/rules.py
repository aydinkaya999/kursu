from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, timedelta
from math import floor

from app.modules.plan.schemas import Assignment, TaskKind

WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
WEEKLY_GOAL = 5
NEAR_EXAM = 30
DAY = timedelta(days=1)


@dataclass
class Topic:
    id: str
    name: str
    subtest: str
    weight: int
    mastery: float
    opened: bool
    lessons: list[tuple[str, str]]
    questions: int


def weight(p1: int, score_type: str) -> float:
    return p1 if score_type == "P1" else p1 / 2


def half_up(value: float) -> int:
    return floor(value + 0.5)


def build(
    *,
    day: date,
    exam: date,
    minutes: int,
    score_type: str,
    mock_weekday: int,
    due: list[str],
    topics: list[Topic],
    mock: tuple[str, str] | None,
    kept: list[Assignment],
    carry: tuple[TaskKind, str] | None = None,
    closed: bool = False,
) -> list[Assignment]:
    budget = minutes * 4
    if day >= exam:
        return kept
    if day.weekday() == mock_weekday:
        if kept or closed:
            return kept
        return (
            [
                Assignment(
                    kind="mock", content_id=mock[0], title=mock[1], count=80, quarters=440
                )
            ]
            if mock
            else []
        )
    result: list[Assignment] = []
    for task in kept:
        if task.kind == "review" and task.quarters > budget * 2 // 5:
            continue
        if sum(t.quarters for t in result) + task.quarters <= budget:
            result.append(task)
    # Actual time already earned still consumes the revised daily budget.
    left = max(0, budget - sum(t.quarters for t in kept))
    if closed or not left:
        return result
    kinds = [a.kind for a in kept]
    if "review" not in kinds and due:
        n = min(len(due), min(budget * 2 // 5, left) // 5)
        if n:
            result.append(
                Assignment(kind="review", count=n, objectives=due[:n], quarters=n * 5)
            )
            left -= n * 5
    near = (exam - day).days <= NEAR_EXAM
    ranked = sorted(
        (t for t in topics if not near or t.opened),
        key=lambda t: (-weight(t.weight, score_type) * (1 - t.mastery), t.id),
    )
    used = {a.topic_id for a in kept if a.kind == "lesson"}
    lessons_left = 2 - kinds.count("lesson")
    lesson_order = sorted(
        ranked,
        key=lambda t: (
            not (
                carry and carry[0] == "lesson" and any(i == carry[1] for i, _ in t.lessons)
            )
        ),
    )
    # In the last month practice opened topics instead of assigning new lessons.
    if not near:
        for topic in lesson_order:
            if lessons_left <= 0 or left < 20:
                break
            if not topic.lessons or topic.id in used:
                continue
            lesson_id, title = next(
                (v for v in topic.lessons if carry == ("lesson", v[0])), topic.lessons[0]
            )
            result.append(
                Assignment(
                    kind="lesson",
                    content_id=lesson_id,
                    title=title,
                    topic_id=topic.id,
                    subtest=topic.subtest,
                    quarters=20,
                )
            )
            lessons_left -= 1
            left -= 20
    if "topic_test" not in kinds:
        test_order = sorted(ranked, key=lambda t: not (carry == ("topic_test", t.id)))
        topic_for_test = next((t for t in test_order if t.questions >= 10), None)
        if topic_for_test:
            n = min(15, left // 6, topic_for_test.questions)
            if n >= 10:
                result.append(
                    Assignment(
                        kind="topic_test",
                        content_id=topic_for_test.id,
                        topic_id=topic_for_test.id,
                        title=topic_for_test.name,
                        subtest=topic_for_test.subtest,
                        count=n,
                        quarters=n * 6,
                    )
                )
    return result


def distribute(today: date, mock_day: int, deadlines: list[date]) -> list[date | None]:
    """Space missed work before each task's exclusive deadline, keeping mock days clear."""
    allocated: dict[date, int] = {}
    slots: list[date | None] = [None] * len(deadlines)
    for i in sorted(range(len(deadlines)), key=deadlines.__getitem__):
        days = [
            today + DAY * n
            for n in range((deadlines[i] - today).days)
            if (today + DAY * n).weekday() != mock_day
        ]
        if not days:
            continue
        target = days[i * len(days) // len(deadlines)]
        chosen = min(days, key=lambda d: (allocated.get(d, 0), abs((d - target).days), d))
        slots[i] = chosen
        allocated[chosen] = allocated.get(chosen, 0) + 1
    return slots


@dataclass
class Streak:
    current: int = 0
    longest: int = 0
    last_completed_on: date | None = None
    freeze_used_week: date | None = None
    weekly_done: int = 0


def streak(first: date, today: date, completed: Iterable[date]) -> Streak:
    done = set(completed)
    result = Streak()
    monday = today - DAY * today.weekday()
    result.weekly_done = min(WEEKLY_GOAL, sum(monday <= d <= today for d in done))
    day = first
    while day <= today:
        week = day - DAY * day.weekday()
        if day in done:
            result.current += 1
            result.longest = max(result.longest, result.current)
            result.last_completed_on = day
        elif day < today:
            if result.freeze_used_week == week:
                result.current = 0
            else:
                result.freeze_used_week = week
        day += DAY
    return result
