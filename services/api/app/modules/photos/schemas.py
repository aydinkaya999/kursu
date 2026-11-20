from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.commerce.schemas import PhotoLimits

MAX_BYTES = 10 * 1024 * 1024


class PhotoUpload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID
    image: str = Field(min_length=4, max_length=4 * ((MAX_BYTES + 2) // 3))


class PhotoPolicy(BaseModel):
    photo_limits: PhotoLimits
    photo_min_confidence: float = Field(ge=0, le=1)
    photo_retention_days: int = Field(gt=0)


class PhotoQuota(BaseModel):
    remaining: int
    period: Literal["lifetime", "day"]


class Step(BaseModel):
    title: str
    text: str


class RelatedLesson(BaseModel):
    id: str
    title: str


class PhotoResult(BaseModel):
    state: Literal["solved", "low_confidence", "out_of_scope"]
    is_placeholder: bool
    question: str | None = None
    steps: list[Step] = Field(default_factory=list)
    answer: str | None = None
    topic: str | None = None
    lesson: RelatedLesson | None = None


class PhotoSolution(BaseModel):
    id: UUID
    result: PhotoResult
    preview_jpeg: str
