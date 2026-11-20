from fastapi import APIRouter, Request

from app.core.http import ISTANBUL, ErrorBody, ServerTime, Session
from app.modules.accounts.security import CurrentUser, signing_key
from app.modules.commerce import access, service
from app.modules.commerce.providers import FakeNativeStore, FakeWebCheckout, sandbox
from app.modules.commerce.schemas import Entitlement, NativePurchase, Paywall, Platform
from app.modules.placement.service import lock_user

router = APIRouter(
    tags=["Commerce"],
    responses={n: {"model": ErrorBody} for n in (401, 403, 409, 422, 503)},
)


@router.get("/paywall", operation_id="getPaywall")
async def paywall(
    db: Session,
    user: CurrentUser,
    now: ServerTime,
    request: Request,
    platform: Platform = "web",
) -> Paywall:
    await lock_user(db, user)
    value = await service.offer(
        db,
        user,
        now,
        platform,
        sandbox(request.app.state.settings.app_env),
        signing_key(request),
    )
    await db.commit()
    return value


@router.get("/entitlements", operation_id="getEntitlements")
async def entitlements(db: Session, user: CurrentUser, now: ServerTime) -> Entitlement:
    return await access.entitlement(db, user, now.astimezone(ISTANBUL).date())


@router.post("/purchases/web/checkout", operation_id="webCheckout")
async def checkout(
    db: Session, user: CurrentUser, now: ServerTime, request: Request
) -> Entitlement:
    await lock_user(db, user)
    provider = FakeWebCheckout() if sandbox(request.app.state.settings.app_env) else None
    result = await service.purchase(db, user, now, None, provider, None)
    await db.commit()
    return result


@router.post("/purchases/native/verify", operation_id="verifyStorePurchase")
async def verify(
    data: NativePurchase, db: Session, user: CurrentUser, now: ServerTime, request: Request
) -> Entitlement:
    await lock_user(db, user)
    provider = (
        FakeNativeStore(signing_key(request))
        if sandbox(request.app.state.settings.app_env)
        else None
    )
    result = await service.purchase(db, user, now, data, None, provider)
    await db.commit()
    return result
