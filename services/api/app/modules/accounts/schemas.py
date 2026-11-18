from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

type ScoreType = Literal["P1", "P2", "P3"]


class GuestRequest(BaseModel):
    platform: Literal["web", "native"]


class RefreshRequest(GuestRequest):
    refresh_token: str | None = None


class Tokens(BaseModel):
    access_token: str
    refresh_token: str | None = None


class ProfileInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field_id: str
    daily_minutes: Literal[30, 60, 90]
    attempt_kind: Literal["first", "repeat"]


class Profile(ProfileInput):
    score_type: ScoreType


class PlacementStatus(BaseModel):
    active_id: UUID | None
    latest_id: UUID | None
    next_retake_on: date | None
    can_retake: bool


class Me(BaseModel):
    id: UUID
    is_guest: bool
    profile: Profile | None
    placement: PlacementStatus
