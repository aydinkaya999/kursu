from datetime import datetime
from typing import Annotated, Literal
from urllib.parse import parse_qs, urlencode
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.http import ApiError, ErrorBody, ServerTime, Session
from app.modules.accounts import providers
from app.modules.accounts.email_login import (
    EmailSender,
    email_sender,
    start_email,
    verify_email,
)
from app.modules.accounts.lifecycle import attach, erase
from app.modules.accounts.models import profiles, refresh_tokens, users
from app.modules.accounts.providers import IdentityProvider, Provider, provider_client
from app.modules.accounts.schemas import (
    EmailStart,
    EmailVerify,
    GuestRequest,
    Preferences,
    ProviderFinish,
    ProviderStart,
    Tokens,
)
from app.modules.accounts.security import COOKIE, CurrentUser, issue, signing_key

router = APIRouter(
    tags=["Accounts"],
    responses={
        400: {"model": ErrorBody},
        401: {"model": ErrorBody},
        404: {"model": ErrorBody},
        409: {"model": ErrorBody},
        422: {"model": ErrorBody},
        429: {"model": ErrorBody},
        503: {"model": ErrorBody},
    },
)
Sender = Annotated[EmailSender, Depends(email_sender)]
Identity = Annotated[IdentityProvider, Depends(provider_client)]


async def sign_in(
    db: AsyncSession,
    request: Request,
    response: Response,
    user: UUID,
    provider: str,
    subject: str,
    platform: str,
    now: datetime,
) -> Tokens:
    account = await attach(db, user, provider, subject)
    tokens = await issue(db, request, response, account, now, platform == "web")
    await db.commit()
    return tokens


@router.post("/auth/email/start", operation_id="startEmail")
async def email_start(
    data: EmailStart,
    user: CurrentUser,
    db: Session,
    now: ServerTime,
    request: Request,
    sender: Sender,
) -> dict[str, bool]:
    await start_email(
        db, user, str(data.email).casefold(), now, signing_key(request), sender
    )
    await db.commit()
    return {"ok": True}


@router.post(
    "/auth/email/verify", operation_id="verifyEmail", response_model_exclude_none=True
)
async def email_verify(
    data: EmailVerify,
    user: CurrentUser,
    db: Session,
    now: ServerTime,
    request: Request,
    response: Response,
) -> Tokens:
    email = str(data.email).casefold()
    await verify_email(db, user, email, data.code, now, signing_key(request))
    return await sign_in(db, request, response, user, "email", email, data.platform, now)


def clear_cookie(response: Response) -> None:
    response.delete_cookie(
        COOKIE, path="/v1/auth", secure=True, httponly=True, samesite="lax"
    )
    response.headers["Cache-Control"] = "no-store"


@router.post("/auth/logout", operation_id="logout")
async def logout(
    user: CurrentUser, db: Session, request: Request, response: Response
) -> dict[str, bool]:
    family = request.state.session_family
    query = delete(refresh_tokens).where(refresh_tokens.c.user_id == user)
    if family:
        query = query.where(refresh_tokens.c.family_id == family)
    await db.execute(update(users).where(users.c.id == user).values(legacy_access=False))
    await db.execute(query)
    await db.commit()
    clear_cookie(response)
    return {"ok": True}


@router.delete("/me", operation_id="deleteAccount")
async def delete_account(
    user: CurrentUser, db: Session, response: Response
) -> dict[str, bool]:
    guest = await db.scalar(
        select(users.c.is_guest).where(users.c.id == user).with_for_update()
    )
    if guest is not False:
        raise ApiError(409, "conflict", "A registered account is required")
    await erase(db, user)
    await db.commit()
    clear_cookie(response)
    return {"ok": True}


@router.get("/me/settings", operation_id="getSettings")
async def get_settings(user: CurrentUser, db: Session) -> Preferences:
    row = (
        (
            await db.execute(
                select(profiles.c.daily_minutes, profiles.c.notification_time).where(
                    profiles.c.user_id == user
                )
            )
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        raise ApiError(409, "conflict", "Complete onboarding first")
    return Preferences.model_validate(row)


@router.patch("/me/settings", operation_id="saveSettings")
async def save_settings(data: Preferences, user: CurrentUser, db: Session) -> Preferences:
    await db.execute(select(users.c.id).where(users.c.id == user).with_for_update())
    if not await db.scalar(
        update(profiles)
        .where(profiles.c.user_id == user)
        .values(**data.model_dump())
        .returning(profiles.c.user_id)
    ):
        raise ApiError(409, "conflict", "Complete onboarding first")
    await db.commit()
    return data


@router.post("/auth/{provider}/start", operation_id="startProvider")
async def provider_start(
    provider: Provider,
    data: GuestRequest,
    user: CurrentUser,
    db: Session,
    now: ServerTime,
    op: Identity,
) -> ProviderStart:
    result = await providers.begin(db, user, data.platform, op, now)
    await db.commit()
    return result


@router.post(
    "/auth/{provider}", operation_id="verifyProvider", response_model_exclude_none=True
)
async def provider_finish(
    provider: Provider,
    data: ProviderFinish,
    user: CurrentUser,
    db: Session,
    now: ServerTime,
    op: Identity,
    request: Request,
    response: Response,
) -> Tokens:
    subject = await providers.take_subject(
        db, user, op, data.state, data.id_token, data.platform, now
    )
    return await sign_in(db, request, response, user, provider, subject, data.platform, now)


async def redirect_back(
    request: Request,
    db: AsyncSession,
    now: datetime,
    op: IdentityProvider,
    state: str,
    code: str,
) -> RedirectResponse:
    platform = await providers.callback(db, op, state, code, now)
    await db.commit()
    dest = (
        request.app.state.settings.app_origin.rstrip("/") + "/auth"
        if platform == "web"
        else "kursu://auth"
    )
    result = RedirectResponse(
        dest
        + "?"
        + urlencode(
            dict(provider=op.provider, state=state, **({} if code else {"cancel": "1"}))
        ),
        status_code=303,
    )
    result.headers.update({"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"})
    return result


@router.get("/auth/callback/{provider}", operation_id="googleCallback")
async def google_callback(
    provider: Literal["google"],
    request: Request,
    db: Session,
    now: ServerTime,
    op: Identity,
    state: str,
    code: str = "",
) -> RedirectResponse:
    return await redirect_back(request, db, now, op, state, code)


@router.post("/auth/callback/{provider}", operation_id="appleCallback")
async def apple_callback(
    provider: Literal["apple"], request: Request, db: Session, now: ServerTime, op: Identity
) -> RedirectResponse:
    form = parse_qs((await request.body()).decode(), max_num_fields=16)
    return await redirect_back(
        request, db, now, op, form.get("state", [""])[0], form.get("code", [""])[0]
    )
