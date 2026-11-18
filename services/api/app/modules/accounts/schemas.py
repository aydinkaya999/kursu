from datetime import date, time
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

type ScoreType = Literal["P1", "P2", "P3"]


class GuestRequest(BaseModel):
    platform: Literal["web", "native"]


class RefreshRequest(GuestRequest):
    refresh_token: str | None = None


class Tokens(BaseModel):
    access_token: str
    refresh_token: str | None = None


class EmailStart(BaseModel):
    email: EmailStr


class EmailVerify(GuestRequest, EmailStart):
    code: str = Field(pattern=r"^[0-9]{6}$")


class ProviderStart(BaseModel):
    authorization_url: str
    state: str
    nonce: str


class ProviderFinish(GuestRequest):
    state: str = Field(min_length=24, max_length=256)
    id_token: str | None = Field(default=None, max_length=12000)


class Preferences(BaseModel):
    daily_minutes: Literal[30, 60, 90]
    notification_time: time | None = None

    @field_validator("notification_time")
    @classmethod
    def clock_minutes(cls, value: time | None) -> time | None:
        if value and (value.tzinfo or value.second or value.microsecond):
            raise ValueError("Use a local hour and minute")
        return value


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
