from uuid import uuid4

from fastapi import APIRouter, Request, Response
from sqlalchemy import insert, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.http import ApiError, ErrorBody, ServerTime, Session
from app.modules.accounts.models import profiles, users
from app.modules.accounts.schemas import (
    GuestRequest,
    Me,
    Profile,
    ProfileInput,
    RefreshRequest,
    Tokens,
)
from app.modules.accounts.security import (
    COOKIE,
    CurrentUser,
    consume_refresh,
    issue,
    unauthorized,
)
from app.modules.content.models import fields
from app.modules.placement.service import placement_status

router = APIRouter(
    tags=["Guests"], responses={401: {"model": ErrorBody}, 422: {"model": ErrorBody}}
)


@router.post("/auth/guest", operation_id="createGuest", response_model_exclude_none=True)
async def create_guest(
    data: GuestRequest,
    request: Request,
    response: Response,
    session: Session,
    now: ServerTime,
) -> Tokens:
    # Resuming a web guest here also makes a repeated bootstrap safe after a lost response.
    web = data.platform == "web"
    cookie = request.cookies.get(COOKIE) if web else None
    if cookie:
        try:
            user = await consume_refresh(session, cookie, now)
        except ApiError:
            user = None
    else:
        user = None
    if user is None:
        user = uuid4()
        await session.execute(insert(users).values(id=user, is_guest=True, created_at=now))
    tokens = await issue(session, request, response, user, now, web)
    await session.commit()
    return tokens


@router.post(
    "/auth/refresh", operation_id="refreshSession", response_model_exclude_none=True
)
async def refresh(
    data: RefreshRequest,
    request: Request,
    response: Response,
    session: Session,
    now: ServerTime,
) -> Tokens:
    web = data.platform == "web"
    raw = request.cookies.get(COOKIE) if web else data.refresh_token
    if not raw:
        raise unauthorized()
    user = await consume_refresh(session, raw, now)
    tokens = await issue(session, request, response, user, now, web)
    await session.commit()
    return tokens


@router.get("/me", operation_id="getMe")
async def me(user: CurrentUser, session: Session, now: ServerTime) -> Me:
    row = (
        (
            await session.execute(
                select(
                    profiles.c.field_id,
                    profiles.c.score_type,
                    profiles.c.daily_minutes,
                    profiles.c.attempt_kind,
                ).where(profiles.c.user_id == user)
            )
        )
        .mappings()
        .one_or_none()
    )
    guest = await session.scalar(select(users.c.is_guest).where(users.c.id == user))
    return Me(
        id=user,
        is_guest=bool(guest),
        profile=Profile.model_validate(row) if row else None,
        placement=await placement_status(session, user, now),
    )


@router.patch("/me/profile", operation_id="saveProfile")
async def save_profile(data: ProfileInput, user: CurrentUser, session: Session) -> Profile:
    score = await session.scalar(
        select(fields.c.score_type).where(fields.c.id == data.field_id)
    )
    if score is None:
        raise ApiError(422, "validation_error", "Unknown teaching field")
    profile = Profile.model_validate({**data.model_dump(), "score_type": score})
    values = profile.model_dump()
    await session.execute(
        pg_insert(profiles)
        .values(user_id=user, **values)
        .on_conflict_do_update(index_elements=[profiles.c.user_id], set_=values)
    )
    await session.commit()
    return profile
