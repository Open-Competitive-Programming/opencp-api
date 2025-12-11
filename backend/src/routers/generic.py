from __future__ import annotations

import functools
import inspect
import time
from logging import Logger, getLogger
from typing import Any, Awaitable, Callable, Optional, Union, TypeVar, Dict
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from exceptions import APIException, DataError 
from starlette.responses import Response
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel

from exceptions import APIException

log = getLogger(__name__)

# ---------- Success envelope ----------
class APIEnvelope(BaseModel):
    help: str
    success: bool = True
    result: Any

def _ok(result: Any, request: Request) -> APIEnvelope:
    return APIEnvelope(help=str(request.url), result=result)

# ---------- Helpers ----------
T = TypeVar("T")
EndpointFn = Union[Callable[..., T], Callable[..., Awaitable[T]]]
ResultMapper = Callable[[Any], Any]

REDACT_KEYS = {
    "password",
    "pwd",
    "token",
    "access_token",
    "authorization",
    "secret",
    "apikey",
    "api_key",
}

def _redact(d: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(d, dict):
        return d  # best effort
    out = {}
    for k, v in d.items():
        if k.lower() in REDACT_KEYS:
            out[k] = "***"
        else:
            out[k] = v
    return out

def _pick_request(args, kwargs, fn) -> Optional[Request]:
    req = kwargs.get("request")
    if isinstance(req, Request):
        return req
    sig = inspect.signature(fn)
    bound = sig.bind_partial(*args, **kwargs)
    for name, param in sig.parameters.items():
        val = bound.arguments.get(name)
        if isinstance(val, Request):
            return val
    return None

# ---------- Decorator ----------
def render(
    map_result: Optional[ResultMapper] = None,
    *,
    logger: Optional[Logger] = None,
    event: Optional[str] = None,
) -> Callable[[EndpointFn], EndpointFn]:
    """
    Wrap an endpoint to:
      - pass through Response objects
      - re-raise APIException for global handlers
      - wrap unknown errors via APIException.from_unexpected
      - envelope successful results uniformly
      - log only on exceptions
    """
    logger = logger or log

    def decorator(func: EndpointFn) -> EndpointFn:
        is_coro = inspect.iscoroutinefunction(func)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            req = _pick_request(args, kwargs, func)
            if req is None:
                raise RuntimeError(
                    "render(): endpoint must accept a 'request: Request' parameter "
                    "to build the success envelope."
                )

            started = time.perf_counter()
            ev = event or func.__name__
            rid = getattr(getattr(req, "state", None), "request_id", None)

            try:
                if is_coro:
                    result = await func(*args, **kwargs)
                else:
                    result = await run_in_threadpool(func, *args, **kwargs)

                if isinstance(result, Response):
                    return result 
                if map_result:
                    result = map_result(result)

                return _ok(result, req)

            except APIException as exc:
                # Log only on exception
                level = 30 if exc.status_code < 500 else 40  # WARNING for 4xx, ERROR for 5xx
                dur = (time.perf_counter() - started) * 1000
                logger.log(
                    level,
                    f"api.api_exception:{ev}",
                    extra={
                        "method": req.method,
                        "path": req.url.path,
                        "status": exc.status_code,
                        "code": getattr(exc, "code", None),
                        "detail": exc.detail,
                        "duration_ms": round(dur, 2),
                        "request_id": rid,
                    },
                    exc_info=exc.status_code >= 500,
                )
                raise  # handled by global APIException handler

            except Exception as exc:
                dur = (time.perf_counter() - started) * 1000
                logger.exception(
                    f"api.unexpected:{ev}",
                    extra={
                        "method": req.method,
                        "path": req.url.path,
                        "duration_ms": round(dur, 2),
                        "request_id": rid,
                    },
                )
                raise APIException.from_unexpected(exc) from exc

        return async_wrapper  # Always return the async wrapper

    return decorator


def install_error_handler(app: FastAPI) -> None:
    """
    Installs exception handlers that render a minimal, uniform error shape:

    {
      "success": false,
      "error": {
         "detail": "...",
         "title": "...",
         "code": "..."
      },
      "help": "<url>"
    }
    """
    @app.exception_handler(APIException)
    async def handle_api_exception(request: Request, exc: APIException):
        return _to_simple_response(request, exc)

    @app.exception_handler(RequestValidationError)
    async def handle_validation(request: Request, exc: RequestValidationError):
        data_error = DataError(
            detail="Validation failed",
            errors=exc.errors(),
            extra={"title": "RequestValidationError"},
        )
        return _to_simple_response(request, data_error)

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception):
        from exceptions import APIException as _APIException
        internal = _APIException.from_unexpected(exc)
        return _to_simple_response(request, internal)

def _to_simple_response(request: Request, exc: APIException):
    """
    Convert any APIException into the minimal shape.
    """
    title = exc.extra.get("title", exc.__class__.__name__)
    code = getattr(exc, "code", None)
    detail = exc.detail

    body = {
        "success": False,
        "error": {
            "title": title,
            "detail": detail,
            "code": code,
        },
        "help": str(request.url),
    }
    from fastapi.responses import JSONResponse
    return JSONResponse(
        body,
        status_code=exc.status_code,
        headers=exc.headers,
    )