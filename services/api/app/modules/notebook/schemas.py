from datetime import date
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator

type GroupBy = Literal["topic", "misconception"]


class ReviewStart(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["review"]
    mode: Literal["due", "early"] = "due"
    group_by: GroupBy | None = None
    group_id: str | None = None
    task_id: UUID | None = None

    @model_validator(mode="after")
    def valid_scope(self) -> Self:
        if (self.group_by is None) != (self.group_id is None):
            raise ValueError("Specify both grouping and group ID")
        if self.task_id and (self.group_by or self.mode == "early"):
            raise ValueError("Planned reviews use the assigned due entries")
        return self


class NotebookGroup(BaseModel):
    id: str
    name: str | None
    subtests: list[str]
    open_count: int = 0
    learned_count: int = 0
    next_due_on: date | None = None
    next_due_days: int | None = None


class NotebookSummary(BaseModel):
    open_count: int
    learned_count: int
    due_today: int
    due_tomorrow: int
    intervals: list[int]
