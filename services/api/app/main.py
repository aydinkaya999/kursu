from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.http import ApiError, ErrorBody, handle_error
from app.core.settings import Settings
from app.modules.accounts.access import router as access_router
from app.modules.accounts.router import router as account_router
from app.modules.content.router import router as catalogue_router
from app.modules.placement.router import router as placement_router
from app.modules.plan.router import router as plan_router
from app.modules.practice.router import router as practice_router
from app.modules.system.config import router as config_router
from app.modules.system.router import router as system_router


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
    application.state.settings = config
    application.add_exception_handler(ApiError, handle_error)

    @application.exception_handler(RequestValidationError)
    async def validation_error(
        request: Request, error: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=ErrorBody(
                code="validation_error",
                message="Invalid request",
                details={"field": ".".join(map(str, error.errors()[0]["loc"]))},
            ).model_dump(),
        )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=[config.app_origin],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )
    application.include_router(system_router, prefix="/v1")
    application.include_router(catalogue_router, prefix="/v1")
    for router in (
        account_router,
        access_router,
        placement_router,
        plan_router,
        practice_router,
        config_router,
    ):
        application.include_router(router, prefix="/v1")
    return application


app = create_app()
