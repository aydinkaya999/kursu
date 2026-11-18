import asyncio
import hmac
import json
import logging
import secrets
import smtplib
import ssl
from datetime import datetime, timedelta
from email.message import EmailMessage
from pathlib import Path
from typing import Protocol
from uuid import UUID

from fastapi import Request
from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.http import ApiError
from app.core.settings import Settings
from app.modules.accounts.models import email_codes


class EmailSender(Protocol):
    def send(self, email: str, code: str) -> None: ...


class DevelopmentSender:
    def send(self, email: str, code: str) -> None:
        logging.getLogger("uvicorn.error").info(
            "Development sign-in code for %s: %s", email, code
        )


class SMTPSender:
    def __init__(self, settings: Settings):
        self.settings = settings

    def send(self, email: str, code: str) -> None:
        cfg = self.settings
        message = EmailMessage()
        message["From"], message["To"] = cfg.email_sender, email
        catalogue = Path(__file__).resolve().parents[5] / "apps/app/src/i18n/email.json"
        copy = json.loads(catalogue.read_text())
        message["Subject"] = copy["subject"]
        message.set_content(copy["body"].format(code=code))
        with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=10) as mail:
            mail.starttls(context=ssl.create_default_context())
            if cfg.smtp_username:
                mail.login(cfg.smtp_username, cfg.smtp_password.get_secret_value())
            mail.send_message(message)


def email_sender(request: Request) -> EmailSender:
    cfg: Settings = request.app.state.settings
    if cfg.smtp_host and cfg.email_sender:
        return SMTPSender(cfg)
    if cfg.production:
        raise ApiError(503, "provider_unavailable", "Email delivery is not configured")
    return DevelopmentSender()


def digest(key: str, user: UUID, email: str, code: str) -> str:
    return hmac.digest(key.encode(), f"{user}:{email}:{code}".encode(), "sha256").hex()


async def start_email(
    db: AsyncSession, user: UUID, email: str, now: datetime, key: str, sender: EmailSender
) -> None:
    await db.execute(
        select(func.pg_advisory_xact_lock(func.hashtextextended("email:" + email, 0)))
    )
    last = await db.scalar(
        select(func.max(email_codes.c.sent_at)).where(email_codes.c.email == email)
    )
    if last and now - last < timedelta(seconds=60):
        raise ApiError(429, "rate_limited", "Wait before requesting another code")
    code = f"{secrets.randbelow(1000000):06d}"
    values = dict(
        code_hash=digest(key, user, email, code),
        sent_at=now,
        expires_at=now + timedelta(minutes=10),
        attempts=0,
    )
    await db.execute(delete(email_codes).where(email_codes.c.expires_at <= now))
    await db.execute(
        insert(email_codes)
        .values(email=email, user_id=user, **values)
        .on_conflict_do_update(index_elements=["email", "user_id"], set_=values)
    )
    try:
        await asyncio.to_thread(sender.send, email, code)
    except (OSError, smtplib.SMTPException) as exc:
        raise ApiError(503, "provider_unavailable", "Email delivery unavailable") from exc


async def verify_email(
    db: AsyncSession, user: UUID, email: str, code: str, now: datetime, key: str
) -> None:
    c = email_codes.c
    where = (c.email == email, c.user_id == user)
    row = (
        (await db.execute(select(email_codes).where(*where).with_for_update()))
        .mappings()
        .one_or_none()
    )
    if row and row["expires_at"] > now and row["attempts"] < 5:
        if hmac.compare_digest(row["code_hash"], digest(key, user, email, code)):
            await db.execute(delete(email_codes).where(*where))
            return
        await db.execute(update(email_codes).where(*where).values(attempts=c.attempts + 1))
        await db.commit()
    raise ApiError(400, "invalid_code", "Code invalid or expired")
