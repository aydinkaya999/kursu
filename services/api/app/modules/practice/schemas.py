from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.content.schemas import (
    LawSource,
    LessonSource,
    LessonSummary,
    NotesSource,
    UnansweredQuestion,
)
from app.modules.placement.schemas import Letter

type PracticeKind = Literal["lesson_check", "topic_test"]
type PracticeState = Literal["question", "feedback", "ready", "completed"]
type MasteryState = Literal["not_started", "in_progress", "solid"]


class PracticeStart(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: PracticeKind
    content_id: str
    task_id: UUID | None = None


class Advance(BaseModel):
    question_id: str


class CompleteLesson(BaseModel):
    session_id: UUID


class Rationale(BaseModel):
    option: Letter
    text: str


class SolutionStep(BaseModel):
    title: str
    text: str


class Feedback(BaseModel):
    question: UnansweredQuestion
    selected: Letter
    correct: Letter
    is_correct: bool
    rationales: list[Rationale]
    source: LawSource | LessonSource | NotesSource
    steps: list[SolutionStep]
    misconception_count: int
    suggest_lesson: bool
    related_lesson_id: str | None
    card_position: int | None


class Practice(BaseModel):
    id: UUID
    kind: PracticeKind
    state: PracticeState
    lesson_id: str | None
    topic_id: str
    subtest: str
    task_id: UUID | None
    position: int
    total: int
    question: UnansweredQuestion | None = None
    feedback: Feedback | None = None


class ReportInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    question_id: str
    text: str = Field(min_length=1, max_length=1000)


class ReportReceipt(BaseModel):
    received: bool


class StudyLesson(LessonSummary):
    completed: bool


class StudyTopic(BaseModel):
    id: str
    name: str
    mastery: MasteryState
    can_practice: bool
    lessons: list[StudyLesson]


class StudySection(BaseModel):
    name: str
    topics: list[StudyTopic]
