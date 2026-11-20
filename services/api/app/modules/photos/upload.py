"""Bound incoming base64 JSON before the framework buffers the request."""

from collections.abc import AsyncGenerator, Callable, Coroutine
from typing import Any

from fastapi import HTTPException, Request, Response
from fastapi.routing import APIRoute

from app.core.http import ApiError
from app.modules.photos.schemas import MAX_BYTES

# Encoded file plus the JSON envelope and request UUID.
MAX_BODY = 4 * ((MAX_BYTES + 2) // 3) + 4096


class PhotoRequest(Request):
    async def stream(self) -> AsyncGenerator[bytes, None]:
        size = 0
        async for chunk in super().stream():
            size += len(chunk)
            if size > MAX_BODY:
                raise HTTPException(413)
            yield chunk


class PhotoRoute(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        handle = super().get_route_handler()

        async def bounded(request: Request) -> Response:
            if request.method != "POST":
                return await handle(request)
            length = request.headers.get("content-length", "")
            try:
                if length.isdecimal() and int(length) > MAX_BODY:
                    raise HTTPException(413)
                return await handle(PhotoRequest(request.scope, request.receive))
            except HTTPException as exc:
                if exc.status_code != 413:
                    raise
                raise ApiError(413, "invalid_photo", "Photo exceeds upload limit") from exc

        return bounded
