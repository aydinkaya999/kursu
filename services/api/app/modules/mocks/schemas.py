from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.content.schemas import (
    LawSource,
    LessonSource,
    NotesSource,
    UnansweredQuestion,
)
from app.modules.placement.schemas import Letter
from app.modules.plan.schemas import NetRange
from app.modules.practice.schemas import MasteryState, Rationale, SolutionStep

type Mode = Literal["timed", "practice"]


class Start(BaseModel):
    mode: Mode


class Save(BaseModel):
    model_config = ConfigDict(extra="forbid")
    selected_option: Letter | None = None
    flagged: bool | None = None


class Position(BaseModel):
    position: int = Field(ge=1, le=80)


class Slot(BaseModel):
    position: int
    subtest: str
    question: UnansweredQuestion | None
    selected_option: Letter | None
    flagged: bool


class Attempt(BaseModel):
    id: UUID
    title: str
    mode: Mode
    position: int
    started_at: datetime
    deadline_at: datetime | None
    submitted_at: datetime | None
    remaining_seconds: int | None
    blank: int
    questions: list[Slot]


class Score(BaseModel):
    correct: int = 0
    wrong: int = 0
    blank: int = 0
    net: float = 0


class SectionScore(Score):
    name: str


class WrongTopic(BaseModel):
    name: str
    count: int


class Result(Score):
    id: UUID
    title: str
    submitted_at: datetime
    mode: Mode
    used_minutes: int
    duration_minutes: int
    total: int
    withdrawn: int
    sections: list[SectionScore]
    wrong_topics: list[WrongTopic]
    priorities: list[str]


class ReviewedQuestion(BaseModel):
    position: int
    question: UnansweredQuestion
    selected: Letter | None
    correct: Letter
    rationales: list[Rationale]
    source: LawSource | LessonSource | NotesSource
    steps: list[SolutionStep]


class History(BaseModel):
    id: UUID
    title: str
    submitted_at: datetime
    net: float


class TopicProgress(BaseModel):
    name: str
    state: MasteryState


class SectionProgress(BaseModel):
    name: str
    mastery_percent: int
    topics: list[TopicProgress]


class Progress(BaseModel):
    days_to_exam: int
    net_range: NetRange | None
    net_change: int | None
    trend: list[float]
    sections: list[SectionProgress]
    history: list[History]
    streak: int
    weekly_done: int
    weekly_goal: int
    detailed: bool
