import logging

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("bookmarks_api")

_STATUS_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    500: "INTERNAL_SERVER_ERROR",
}


def _error_response(
    status_code: int,
    code: str,
    message: str,
    details: dict | None = None,
) -> JSONResponse:
    body: dict = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=body)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    code = _STATUS_CODES.get(exc.status_code, "ERROR")
    logger.warning(
        "HTTP %s %s — %s: %s",
        exc.status_code,
        request.url.path,
        code,
        exc.detail,
    )
    return _error_response(exc.status_code, code, str(exc.detail))


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = exc.errors()
    if not errors:
        return _error_response(422, "VALIDATION_ERROR", "Validation failed")

    first = errors[0]
    loc = first.get("loc", ())
    field = ".".join(str(part) for part in loc if part not in ("header", "body", "query", "path"))
    message = first.get("msg", "Validation error")
    constraint = first.get("type", "")
    ctx = first.get("ctx", {})

    details: dict = {"field": field, "constraint": constraint}
    for key, val in ctx.items():
        if isinstance(val, (str, int, float, bool)):
            details[key] = val

    logger.warning(
        "VALIDATION_ERROR %s — field=%r constraint=%r message=%r",
        request.url.path,
        field,
        constraint,
        message,
    )
    return _error_response(422, "VALIDATION_ERROR", message, details)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unhandled %s on %s: %s",
        type(exc).__name__,
        request.url.path,
        exc,
        exc_info=exc,
    )
    return _error_response(500, "INTERNAL_SERVER_ERROR", "An unexpected error occurred")
