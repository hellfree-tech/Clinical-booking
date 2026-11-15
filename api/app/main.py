from __future__ import annotations

import hmac
import json
import logging
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import APIRouter, Depends, FastAPI, Header, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from starlette.exceptions import HTTPException as StarletteHTTPException

from .bookings_service import BookingsService
from .config import Config, load_config
from .database import Database
from .demo_seed import seed_if_empty
from .errors import ApiError, ApiResult
from .idempotency import IdempotencyStore
from .rate_limiter import RateLimiter
from .schemas import NEW_BOOKING_BODY, RESET_BODY, Booking, BookingPage, ErrorOut, ResetOut, SlotList, errors
from .slots_service import SlotsService

MAX_BODY_BYTES = 100 * 1024
logger = logging.getLogger("http")

DESCRIPTION = """
Lets patients list appointment slots, book one, look it up, cancel it, and page through their bookings.

Everything is JSON. Every error response looks like `{"error": "<message>"}`.

Every request needs the `X-API-Key` header; a missing or wrong key returns **401**.
Click **Authorize** and enter the key to try requests from this page.
"""

TAGS = [
    {"name": "Slots", "description": "Browse available appointment slots"},
    {"name": "Bookings", "description": "Book, look up, list and cancel bookings"},
    {"name": "Admin", "description": "⚠️ Destructive operations for admins and automated tests. Not for patients."},
]

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False, scheme_name="apiKey")


def send(result: ApiResult) -> JSONResponse:
    return JSONResponse(result.body, status_code=result.status, headers=result.headers)


async def read_json(request: Request):
    raw = await request.body()
    if len(raw) > MAX_BODY_BYTES:
        raise ApiError(413, "request body is too large")
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except ValueError:
        raise ApiError(400, "request body is not valid JSON")


def create_app(config: Optional[Config] = None) -> FastAPI:
    config = config or load_config()

    db = Database(config.db_path)
    slots = SlotsService(db)
    limiter = RateLimiter(config.rate_limit_max, config.rate_limit_window_ms)
    bookings = BookingsService(db, slots, limiter, IdempotencyStore(db, config.idempotency_ttl_ms))
    expected_key = config.api_key.encode()

    async def require_api_key(key: Optional[str] = Depends(api_key_header)) -> None:
        if not key:
            raise ApiError(401, "missing API key")
        if not hmac.compare_digest(key.encode(), expected_key):
            raise ApiError(401, "invalid API key")

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if config.seed_on_start:
            seed_if_empty(db)
        yield
        db.close()

    app = FastAPI(
        lifespan=lifespan,
        title="Clinic Booking API (v2 · FastAPI)",
        description=DESCRIPTION,
        version="2.0",
        openapi_tags=TAGS,
        swagger_ui_parameters={"persistAuthorization": True},
    )
    app.state.db = db

    # ---- errors: always {"error": "..."} ----
    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError):
        return JSONResponse({"error": exc.message}, status_code=exc.status)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException):
        return JSONResponse({"error": str(exc.detail).lower()}, status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError):
        first = exc.errors()[0] if exc.errors() else {}
        where = ".".join(str(p) for p in first.get("loc", [])[1:]) or "request"
        return JSONResponse({"error": f"{where}: {first.get('msg', 'invalid')}"}, status_code=400)

    @app.exception_handler(Exception)
    async def _unexpected(_: Request, exc: Exception):
        logger.exception("unhandled error", exc_info=exc)
        return JSONResponse({"error": "internal server error"}, status_code=500)

    # ---- middleware ----
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        if config.log_requests:
            # Path only, so emails in query strings stay out of logs.
            logger.info("%s %s %s %.1fms", request.method, request.url.path, response.status_code, (time.perf_counter() - started) * 1000)
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if config.cors_origins == "*" else config.cors_origins,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type", "X-API-Key", "Idempotency-Key"],
        expose_headers=["Retry-After"],
    )

    unauthorized = errors((401, "Missing or wrong X-API-Key"))
    secured = APIRouter(dependencies=[Depends(require_api_key)], responses=unauthorized)

    # ---- slots ----
    @secured.get("/slots", tags=["Slots"], response_model=SlotList, summary="Level 1 · List slots",
                 description="Every slot, earliest `start` first.")
    async def list_slots(provider: Optional[str] = Query(None, description="Only this provider's slots (exact match)")):
        return {"slots": slots.list(provider)}

    # ---- bookings ----
    @secured.post(
        "/bookings",
        tags=["Bookings"],
        status_code=201,
        response_model=Booking,
        summary="Book a slot (levels 1–5)",
        description="\n\n".join([
            "**Level 1:** returns 201 with the booking, status `confirmed`.",
            "**Level 2:** **400** if `slot_id`, `name` or `email` is missing or empty, or the email isn't valid. "
            "**404** if the slot doesn't exist. **400** if the slot has already started. "
            "`name` and `email` are trimmed and `email` is stored in lower case.",
            "**Level 3:** a slot that already has a confirmed booking returns **409**, even when many requests arrive at once.",
            "**Level 4:** optional `Idempotency-Key` header. Same key + same body returns the same response and booking `id`. "
            "Same key + different body returns **422**.",
            "**Level 5:** at most 5 attempts per email per minute, failed attempts included. "
            "The 6th returns **429** with a `Retry-After` header in whole seconds.",
        ]),
        openapi_extra={"requestBody": NEW_BOOKING_BODY},
        responses={
            **errors(
                (400, "Missing or invalid field, or the slot has already started"),
                (404, "The slot doesn't exist"),
                (409, "Slot already booked"),
                (422, "Idempotency-Key reused with a different body"),
            ),
            429: {
                "model": ErrorOut,
                "description": "Too many attempts for this email",
                "headers": {"Retry-After": {"description": "Seconds to wait", "schema": {"type": "integer"}}},
            },
        },
    )
    async def create_booking(request: Request, idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")):
        body = await read_json(request)
        # Everything below is synchronous: no other request can interleave.
        return send(bookings.create(body, idempotency_key))

    @secured.get(
        "/bookings",
        tags=["Bookings"],
        response_model=BookingPage,
        summary="Level 4 · List a person's bookings",
        description="That person's bookings, oldest first. The email match ignores case. "
        "Pass `next_cursor` back as `cursor` for the next page; the last page has `next_cursor: null`.",
        responses=errors((400, "Missing email, invalid limit or invalid cursor")),
    )
    async def list_bookings(
        email: Optional[str] = Query(None),
        limit: Optional[str] = Query(None, description="1 to 50 (default 10). Anything else returns 400."),
        cursor: Optional[str] = Query(None),
    ):
        return send(bookings.list_by_email(email, limit, cursor))

    @secured.get("/bookings/{booking_id}", tags=["Bookings"], response_model=Booking, summary="Level 1 · Get a booking",
                 responses=errors((404, "No booking with that id")))
    async def get_booking(booking_id: str):
        return send(bookings.get(booking_id))

    @secured.delete(
        "/bookings/{booking_id}",
        tags=["Bookings"],
        response_model=Booking,
        summary="Level 3 · Cancel a booking",
        description="Sets `status` to `cancelled` and frees the slot.",
        responses=errors((404, "No booking with that id"), (409, "Already cancelled")),
    )
    async def cancel_booking(booking_id: str):
        return send(bookings.cancel(booking_id))

    # ---- admin ----
    @secured.post(
        "/reset",
        tags=["Admin"],
        response_model=ResetOut,
        summary="⚠️ Admin · Replace all slots (destructive)",
        description="**⚠️ Deletes every booking.** Admin and testing only. Not for patients, and not reachable through the web app.\n\n"
        "Replaces all slots with the ones you send, including slots in the past. It also clears saved idempotency keys "
        "and rate-limit counters. (Spec level 1.)",
        openapi_extra={"requestBody": RESET_BODY},
        responses=errors((400, "Invalid slots payload")),
    )
    async def reset(request: Request):
        parsed = slots.parse_reset_body(await read_json(request))
        slots.replace_all(parsed)
        limiter.clear()
        return {"ok": True, "slots": len(parsed)}

    app.include_router(secured)

    @app.get("/health", include_in_schema=False)
    async def health():
        return {"status": "ok"}

    return app

