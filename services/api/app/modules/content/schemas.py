"""Public catalogue shapes. Feedback is private to the question bank."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class TeachingField(BaseModel):
    id: str
    name: str
    score_type: Literal["P1", "P2", "P3"]


class Subtest(BaseModel):
    id: str
    name: str
    short_name: str
    question_count: int
    exam_order: int
    weight_p1: int


class Topic(BaseModel):
    id: str
    subtest_id: str
    name: str
    exam_weight: float | None
    is_placeholder: bool


class LessonSummary(BaseModel):
    id: str
    topic_id: str
    title: str
    minutes: int
    is_placeholder: bool


class LessonCardBlock(BaseModel):
    heading: str
    text: str


class LessonCard(BaseModel):
    position: int
    kind: Literal["definition", "example", "confused", "exam"]
    title: str
    blocks: list[LessonCardBlock]
    tip: str | None


class QuestionOptions(BaseModel):
    A: str
    B: str
    C: str
    D: str
    E: str


class UnansweredQuestion(BaseModel):
    id: str
    stem: str
    options: QuestionOptions


class LawSource(BaseModel):
    kind: Literal["law"]
    short_name: str
    name: str | None = None
    article: int | None = None
    articles: list[int] | None = None
    quote: str | None = None


class NotesSource(BaseModel):
    kind: Literal["notes"]
    title: str
    section: str


class LessonSource(BaseModel):
    kind: Literal["lesson"]
    lesson_title: str


class LessonDetail(LessonSummary):
    source: LawSource | NotesSource | LessonSource
    cards: list[LessonCard]
    check_questions: list[UnansweredQuestion]


class MockSummary(BaseModel):
    id: str
    title: str
    published_at: datetime | None
    is_placeholder: bool


class NotFound(BaseModel):
    code: Literal["not_found"]
    message: str
    details: dict[str, str]
