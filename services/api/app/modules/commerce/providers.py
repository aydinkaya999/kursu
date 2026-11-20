"""Deployment adapters for one-time, account-bound purchases."""

import hashlib
import hmac
from datetime import date
from typing import Protocol
from uuid import UUID

from app.core.http import ApiError
from app.modules.commerce.schemas import Native


class WebCheckoutProvider(Protocol):
    def checkout(self, user: UUID, season: date, amount: int) -> str: ...


class NativePurchaseVerifier(Protocol):
    def verify(self, user: UUID, season: date, platform: Native, receipt: str) -> str: ...


class FakeWebCheckout:
    def checkout(self, user: UUID, season: date, amount: int) -> str:
        return f"test-web/{user}/{season}/{amount}"


class FakeNativeStore:
    def __init__(self, secret: str):
        self.secret = secret.encode()

    def receipt(self, user: UUID, season: date, platform: Native) -> str:
        message = f"test-purchase/{platform}/{user}/{season}".encode()
        return hmac.new(self.secret, message, hashlib.sha256).hexdigest()

    def verify(self, user: UUID, season: date, platform: Native, receipt: str) -> str:
        if not hmac.compare_digest(
            receipt.encode(), self.receipt(user, season, platform).encode()
        ):
            raise ApiError(
                422,
                "validation_error",
                "Store receipt does not match this account and season",
            )
        return receipt


def sandbox(environment: str) -> bool:
    return environment.strip().lower() in {"development", "test"}
