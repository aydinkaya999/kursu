from dataclasses import dataclass
from datetime import date, timedelta


def entry_key(objective: str, misconception: str | None) -> str:
    return f"{objective}/{misconception}" if misconception else objective


def qualifies(correct: bool | None, unsure: bool) -> bool:
    return correct is False or unsure


@dataclass(frozen=True)
class Calendar:
    exam: date
    regular: tuple[int, ...]

    def intervals(self, day: date) -> tuple[int, ...]:
        return (1, 2, 3, 5) if 0 <= (self.exam - day).days < 14 else self.regular

    def due(self, since: date, index: int, today: date) -> date:
        intervals = self.intervals(today)
        due = since + timedelta(days=intervals[min(index, len(intervals) - 1)])
        if 0 <= (self.exam - today).days < 14:
            return min(due, self.exam - timedelta(days=1))
        return due


@dataclass(frozen=True)
class Schedule:
    scheduled_on: date
    interval_index: int
    correct_streak: int
    due_on: date | None

    def effective_due(self, calendar: Calendar, day: date) -> date | None:
        if self.due_on is None:
            return None
        return min(self.due_on, calendar.due(self.scheduled_on, self.interval_index, day))


def transition(
    calendar: Calendar,
    day: date,
    previous: Schedule | None,
    *,
    review: bool,
    correct: bool | None,
) -> Schedule:
    if review and previous and correct is None:
        return previous
    if review and correct and previous:
        streak = min(3, previous.correct_streak + 1)
        index = min(previous.interval_index + 1, len(calendar.intervals(day)) - 1)
        return Schedule(
            day, index, streak, None if streak == 3 else calendar.due(day, index, day)
        )
    due = calendar.due(day, 0, day)
    if previous and not review:
        due = min(due, previous.effective_due(calendar, day) or due)
    return Schedule(day, 0, 0, due)
