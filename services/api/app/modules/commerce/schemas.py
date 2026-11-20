from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

type Platform = Literal["web", "ios", "android"]
type Native = Literal["ios", "android"]
type Allowance = Annotated[int, Field(ge=0, strict=True)]
type Price = Annotated[int, Field(gt=0, strict=True)]


class Limits(BaseModel):
    plan_days: Allowance
    lessons_per_day: Allowance
    questions_per_day: Allowance
    mock_exams: Allowance


class AccessConfig(BaseModel):
    exam_date: date
    free_limits: Limits


class Config(AccessConfig):
    results_date: date
    web_price_groups_try: list[Price] = Field(min_length=3, max_length=3)
    native_prices_try: dict[Native, Price]


class Entitlement(BaseModel):
    active: bool
    valid_until: date | None
    source: Platform | None


class Paywall(BaseModel):
    results_date: date
    limits: Limits
    amount_try: int
    platform: Platform
    access: Entitlement
    checkout_available: bool
    sandbox_receipt: str | None


class NativePurchase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    platform: Native
    receipt: str = Field(min_length=1, max_length=2048)
