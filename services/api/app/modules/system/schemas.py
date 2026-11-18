from typing import Literal

from pydantic import BaseModel


class Health(BaseModel):
    status: Literal["ok"]


class ServiceUnavailable(BaseModel):
    code: Literal["service_unavailable"]
    message: str
    details: dict[str, object]
