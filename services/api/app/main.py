from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.settings import Settings
from app.modules.system.router import router


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or Settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        from app.core.db import Database

        database = Database(config.database_url)
        application.state.database = database
        try:
            yield
        finally:
            await database.engine.dispose()

    application = FastAPI(
        title="Kürsü API",
        version="0.1.0",
        lifespan=lifespan,
        openapi_url="/v1/openapi.json",
        docs_url="/v1/docs",
        redoc_url=None,
        swagger_ui_oauth2_redirect_url=None,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[config.app_origin],
        allow_credentials=True,
        allow_methods=["GET"],
    )
    application.include_router(router, prefix="/v1")
    return application


app = create_app()
