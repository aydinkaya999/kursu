from datetime import datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe
from typing import Annotated
from uuid import UUID, uuid4

import jwt
from fastapi import Depends, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.http import ApiError, Session
from app.core.settings import Settings
from app.modules.accounts.models import refresh_tokens, users
from app.modules.accounts.schemas import Tokens

COOKIE = "kursu_refresh"
REFRESH_TTL = timedelta(days=30)
ACCESS_TTL = timedelta(minutes=15)
bearer = HTTPBearer(auto_error=False)


def signing_key(request: Request) -> str:
    settings: Settings = request.app.state.settings
    key = settings.jwt_secret.get_secret_value()
    if len(key.encode()) < 32:
        raise ApiError(503, "service_unavailable", "Signing key is not configured")
    return key


def unauthorized() -> ApiError:
    return ApiError(401, "unauthenticated", "A valid session is required")


async def current_user(
    request: Request,
    session: Session,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> UUID:
    if credentials is None:
        raise unauthorized()
    try:
        claims = jwt.decode(
            credentials.credentials,
            signing_key(request),
            algorithms=["HS256"],
            issuer="kursu",
            options={"require": ["exp", "sub", "iat"]},
        )
        user_id = UUID(claims["sub"])
        family = UUID(claims["sid"]) if "sid" in claims else None
    except (jwt.InvalidTokenError, ValueError, TypeError) as error:
        raise unauthorized() from error
    policy = (
        select(refresh_tokens.c.id)
        .where(
            refresh_tokens.c.user_id == user_id,
            refresh_tokens.c.family_id == family,
            refresh_tokens.c.revoked_at.is_(None),
        )
        .exists()
        if family
        else users.c.legacy_access
    )
    if (
        await session.scalar(
            select(users.c.id).where(
                users.c.id == user_id, users.c.deleted_at.is_(None), policy
            )
        )
        is None
    ):
        raise unauthorized()
    request.state.session_family = family
    return user_id


CurrentUser = Annotated[UUID, Depends(current_user)]


async def consume_refresh(
    session: AsyncSession, raw: str, now: datetime
) -> tuple[UUID, UUID]:
    token_hash = sha256(raw.encode()).hexdigest()
    await session.execute(
        select(users.c.id)
        .where(
            users.c.id
            == select(refresh_tokens.c.user_id)
            .where(refresh_tokens.c.token_hash == token_hash)
            .scalar_subquery()
        )
        .with_for_update()
    )
    row = (
        await session.execute(
            update(refresh_tokens)
            .where(
                refresh_tokens.c.token_hash == token_hash,
                refresh_tokens.c.revoked_at.is_(None),
                refresh_tokens.c.expires_at > now,
                refresh_tokens.c.user_id.in_(
                    select(users.c.id).where(users.c.deleted_at.is_(None))
                ),
            )
            .values(revoked_at=now)
            .returning(refresh_tokens.c.user_id, refresh_tokens.c.family_id)
        )
    ).one_or_none()
    if row is None:
        raise unauthorized()
    return row.user_id, row.family_id


async def issue(
    session: AsyncSession,
    request: Request,
    response: Response,
    user: UUID,
    now: datetime,
    web: bool,
    family: UUID | None = None,
) -> Tokens:
    family = family or uuid4()
    access = jwt.encode(
        {
            "sub": str(user),
            "sid": str(family),
            "iss": "kursu",
            "iat": now,
            "exp": now + ACCESS_TTL,
        },
        signing_key(request),
        algorithm="HS256",
    )
    raw = token_urlsafe(48)
    await session.execute(
        insert(refresh_tokens).values(
            id=uuid4(),
            user_id=user,
            family_id=family,
            token_hash=sha256(raw.encode()).hexdigest(),
            expires_at=now + REFRESH_TTL,
        )
    )
    if web:
        response.set_cookie(
            COOKIE,
            raw,
            max_age=int(REFRESH_TTL.total_seconds()),
            httponly=True,
            secure=True,
            samesite="lax",
            path="/v1/auth",
        )
    response.headers["Cache-Control"] = "no-store"
    return Tokens(access_token=access, refresh_token=None if web else raw)
