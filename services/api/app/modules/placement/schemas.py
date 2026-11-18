from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.content.schemas import UnansweredQuestion

type Kind = Literal["full", "short"]
type Letter = Literal["A", "B", "C", "D", "E"]


class Start(BaseModel):
    kind: Kind = "full"


class Submission(BaseModel):
    model_config = ConfigDict(extra="forbid")
    client_answer_id: UUID
    question_id: str
    selected_option: Letter | None
    not_sure: bool = False


class Placement(BaseModel):
    id: UUID
    kind: Kind
    state: Literal["active", "completed"]
    position: int
    total: int
    subtest: str | None
    question: UnansweredQuestion | None


class Breakdown(BaseModel):
    subtest_id: str
    name: str
    correct: int
    asked: int
    priority: bool


class FocusTopic(BaseModel):
    subtest: str
    topic: str


class WeekPreview(BaseModel):
    daily_minutes: int
    topics: list[FocusTopic]
    mock_day: Literal[
        "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
    ]


class PlacementResult(BaseModel):
    id: UUID
    kind: Kind
    total: int
    exam_questions: int
    net_low: int
    net_high: int
    subtests: list[Breakdown]
    first_week: WeekPreview
