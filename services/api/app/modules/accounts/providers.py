import asyncio
import base64
import hashlib
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Literal
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request as URLRequest
from urllib.request import urlopen
from uuid import UUID

import jwt
from fastapi import Request
from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.http import ApiError
from app.core.settings import Settings
from app.modules.accounts.models import provider_challenges as challenges
from app.modules.accounts.schemas import ProviderStart

type Provider = Literal["google", "apple"]


@dataclass(frozen=True)
class Endpoints:
    authorize: str
    token: str
    keys: str
    issuers: tuple[str, ...]


PROVIDERS = {
    "google": Endpoints(
        "https://accounts.google.com/o/oauth2/v2/auth",
        "https://oauth2.googleapis.com/token",
        "https://www.googleapis.com/oauth2/v3/certs",
        ("https://accounts.google.com", "accounts.google.com"),
    ),
    "apple": Endpoints(
        "https://appleid.apple.com/auth/authorize",
        "https://appleid.apple.com/auth/token",
        "https://appleid.apple.com/auth/keys",
        ("https://appleid.apple.com",),
    ),
}


@lru_cache(maxsize=2)
def keyset(url: str) -> jwt.PyJWKClient:
    return jwt.PyJWKClient(url, timeout=8)


class IdentityProvider:
    def __init__(self, provider: Provider, cfg: Settings):
        self.provider = provider
        self.endpoints = PROVIDERS[provider]
        ids = cfg.google_client_ids if provider == "google" else cfg.apple_audiences
        self.audiences = [item.strip() for item in ids.split(",") if item.strip()]
        self.secret = (
            cfg.google_client_secret if provider == "google" else cfg.apple_client_secret
        ).get_secret_value()
        self.callback = cfg.api_public_origin.rstrip("/") + "/v1/auth/callback/" + provider

    def authorize(self, state: str, nonce: str, verifier: str) -> str:
        if not self.audiences or not self.secret:
            raise ApiError(
                503, "provider_unavailable", "Provider credentials are not configured"
            )
        params = dict(
            client_id=self.audiences[0],
            redirect_uri=self.callback,
            response_type="code",
            state=state,
            nonce=nonce,
        )
        if self.provider == "google":
            challenge = (
                base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
                .decode()
                .rstrip("=")
            )
            params.update(
                scope="openid", code_challenge=challenge, code_challenge_method="S256"
            )
        else:
            params.update(response_mode="form_post")
        return self.endpoints.authorize + "?" + urlencode(params)

    def exchange(self, code: str, verifier: str) -> str:
        data = dict(
            grant_type="authorization_code",
            code=code,
            client_id=self.audiences[0],
            client_secret=self.secret,
            redirect_uri=self.callback,
        )
        if self.provider == "google":
            data["code_verifier"] = verifier
        try:
            with urlopen(
                URLRequest(self.endpoints.token, data=urlencode(data).encode()), timeout=8
            ) as response:
                token = json.load(response)["id_token"]
        except HTTPError as exc:
            raise ApiError(
                400, "invalid_identity", "Provider declined this authorization"
            ) from exc
        except (OSError, URLError, KeyError, ValueError) as exc:
            raise ApiError(503, "provider_unavailable", "Provider unavailable") from exc
        return str(token)

    def signing_key(self, token: str) -> Any:
        return keyset(self.endpoints.keys).get_signing_key_from_jwt(token).key

    def verify(self, token: str, nonce: str) -> str:
        if not self.audiences:
            raise ApiError(503, "provider_unavailable", "Provider is not configured")
        try:
            claims = jwt.decode(
                token,
                self.signing_key(token),
                algorithms=["RS256"],
                issuer=self.endpoints.issuers,
                audience=self.audiences,
                options={"require": ["iss", "aud", "exp", "iat", "sub", "nonce"]},
            )
            if not secrets.compare_digest(str(claims["nonce"]), nonce) or not claims["sub"]:
                raise ValueError("Invalid nonce or subject")
            if "azp" in claims and claims["azp"] not in self.audiences:
                raise ValueError("Invalid authorized party")
            return str(claims["sub"])
        except jwt.PyJWKClientConnectionError as exc:
            raise ApiError(
                503, "provider_unavailable", "Provider keys unavailable"
            ) from exc
        except (jwt.PyJWTError, ValueError, TypeError) as exc:
            raise ApiError(400, "invalid_identity", "Identity token rejected") from exc


def provider_client(provider: Provider, request: Request) -> IdentityProvider:
    return IdentityProvider(provider, request.app.state.settings)


async def begin(
    db: AsyncSession, user: UUID, platform: str, op: IdentityProvider, now: datetime
) -> ProviderStart:
    state, nonce, verifier = (secrets.token_urlsafe(40) for _ in range(3))
    url = op.authorize(state, nonce, verifier)
    await db.execute(delete(challenges).where(challenges.c.expires_at <= now))
    await db.execute(
        insert(challenges).values(
            state=state,
            provider=op.provider,
            user_id=user,
            platform=platform,
            nonce=nonce,
            pkce_verifier=verifier,
            expires_at=now + timedelta(minutes=10),
        )
    )
    return ProviderStart(authorization_url=url, state=state, nonce=nonce)


async def callback(
    db: AsyncSession, op: IdentityProvider, state: str, code: str, now: datetime
) -> str:
    row = (
        (
            await db.execute(
                select(challenges)
                .where(
                    challenges.c.state == state,
                    challenges.c.provider == op.provider,
                    challenges.c.expires_at > now,
                    challenges.c.subject.is_(None),
                )
                .with_for_update()
            )
        )
        .mappings()
        .one_or_none()
    )
    if not row:
        raise ApiError(400, "invalid_identity", "Authorization expired")
    if code:
        token = await asyncio.to_thread(op.exchange, code, row["pkce_verifier"])
        subject = await asyncio.to_thread(op.verify, token, row["nonce"])
        await db.execute(
            update(challenges).where(challenges.c.state == state).values(subject=subject)
        )
    return str(row["platform"])


async def take_subject(
    db: AsyncSession,
    user: UUID,
    op: IdentityProvider,
    state: str,
    token: str | None,
    platform: str,
    now: datetime,
) -> str:
    row = (
        await db.execute(
            delete(challenges)
            .where(
                challenges.c.state == state,
                challenges.c.provider == op.provider,
                challenges.c.user_id == user,
                challenges.c.platform == platform,
                challenges.c.expires_at > now,
            )
            .returning(challenges.c.nonce, challenges.c.subject)
        )
    ).one_or_none()
    if row:
        if token:
            return await asyncio.to_thread(op.verify, token, row.nonce)
        if row.subject:
            return str(row.subject)
    raise ApiError(400, "invalid_identity", "Authorization expired or incomplete")
