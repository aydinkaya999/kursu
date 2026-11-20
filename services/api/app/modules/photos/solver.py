from functools import lru_cache
from pathlib import Path
from typing import Literal, Protocol

from fastapi import Request
from pydantic import BaseModel, Field

from app.core.http import ApiError
from app.modules.photos.schemas import Step

type StubMode = Literal["solved", "low_confidence", "out_of_scope"]


class Reading(BaseModel):
    in_scope: bool
    confidence: float = Field(ge=0, le=1)
    topic_id: str | None
    question: str
    steps: list[Step]
    answer: str
    is_placeholder: bool = False


class VisionSolver(Protocol):
    async def solve(self, image: bytes) -> Reading: ...


@lru_cache(maxsize=1)
def example() -> Reading:
    path = Path(__file__).resolve().parents[5] / "content/seed/photo-example.json"
    return Reading.model_validate_json(path.read_bytes())


class StubVisionSolver:
    def __init__(self, mode: StubMode) -> None:
        self.mode = mode

    async def solve(self, image: bytes) -> Reading:
        return example().model_copy(
            update={
                "in_scope": self.mode != "out_of_scope",
                "confidence": 0.1 if self.mode == "low_confidence" else 1.0,
            }
        )


def vision_solver(request: Request) -> VisionSolver:
    settings = request.app.state.settings
    if settings.app_env not in {"development", "test"}:
        raise ApiError(503, "service_unavailable", "Vision provider is not configured")
    return StubVisionSolver(settings.photo_stub_mode)
