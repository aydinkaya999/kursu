"""Initialize the local signing key on fresh and pre-M3 development checkouts."""

import os
import secrets
from pathlib import Path

from dotenv import dotenv_values

path = Path(".env")
values = dotenv_values(path)
if not (os.environ.get("JWT_SECRET") or values.get("JWT_SECRET")):
    if (os.environ.get("APP_ENV") or values.get("APP_ENV")) == "production":
        raise SystemExit("Set JWT_SECRET in the production environment.")
    lines = path.read_text().splitlines()
    lines = [line for line in lines if not line.startswith("JWT_SECRET=")]
    lines.append("JWT_SECRET=" + secrets.token_urlsafe(48))
    path.write_text("\n".join(lines) + "\n")
