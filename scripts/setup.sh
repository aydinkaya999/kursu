#!/bin/sh
set -eu

if [ ! -f .env ]; then
  cp .env.example .env
fi

pnpm install --frozen-lockfile
uv sync --locked --directory services/api
docker compose up --detach --wait postgres
uv run --directory services/api alembic upgrade head
pnpm import-content content/seed/config.json content/seed/sample-content.json
pnpm make-placeholders
pnpm gen:api
pnpm --filter @kursu/app exec playwright install chromium
