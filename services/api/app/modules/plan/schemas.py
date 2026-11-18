from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

type TaskKind = Literal["review", "lesson", "topic_test", "mock"]


class Assignment(BaseModel):
    kind: TaskKind
    content_id: str | None = None
    title: str | None = None
    topic_id: str | None = None
    subtest: str | None = None
    count: int = 0
    objectives: list[str] = Field(default_factory=list)
    quarters: int

    @property
    def key(self) -> str:
        return self.kind + ":" + (self.content_id or "")


class PlanTask(BaseModel):
    id: UUID
    kind: TaskKind
    content_id: str | None
    title: str | None
    subtest: str | None
    count: int
    minutes: float
    state: Literal["pending", "started", "done"]
    is_next: bool


class Priority(BaseModel):
    name: str
    mastery_percent: int


class NetRange(BaseModel):
    low: int
    high: int


class Today(BaseModel):
    plan_date: date
    days_to_exam: int
    daily_minutes: int
    mock_day: bool
    tasks: list[PlanTask]
    earlier_completed: list[PlanTask]
    total: int
    done: int
    percent: int
    day_completed: bool
    remaining_minutes: float
    streak: int
    weekly_done: int
    weekly_goal: int
    net_range: NetRange | None
    net_change: int | None
    priorities: list[Priority]
