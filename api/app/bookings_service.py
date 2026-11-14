from __future__ import annotations

import sqlite3
import uuid
from typing import Any, Optional

from .database import Database
from .errors import ApiResult, fail, ok
from .idempotency import IdempotencyStore
from .rate_limiter import RateLimiter, now_ms
from .slots_service import SlotsService
from .utils import (
    DEFAULT_PAGE_SIZE,
    EMAIL_RE,
    MAX_EMAIL,
    MAX_IDEMPOTENCY_KEY,
    MAX_NAME,
    MAX_PAGE_SIZE,
    REQUIRED_FIELDS,
    booking_dict,
    decode_cursor,
    encode_cursor,
    iso_now,
)


class BookingsService:
    """Synchronous and called from async handlers, so each request runs atomically on the event loop."""

    def __init__(self, db: Database, slots: SlotsService, rate_limiter: RateLimiter, idempotency: IdempotencyStore):
        self.db = db
        self.slots = slots
        self.rate_limiter = rate_limiter
        self.idempotency = idempotency

    def create(self, body: Any, idempotency_key: Optional[str]) -> ApiResult:
        """Idempotency replay → rate limit → validate → book."""
        if idempotency_key is None:
            return self._rate_limited(body) or self._book(body)

        if not idempotency_key.strip() or len(idempotency_key) > MAX_IDEMPOTENCY_KEY:
            return fail(400, f"Idempotency-Key must be 1-{MAX_IDEMPOTENCY_KEY} characters")
        fingerprint = self.idempotency.fingerprint(body)
        kind, previous = self.idempotency.lookup(idempotency_key, fingerprint)
        if kind == "replay":
            return previous
        if kind == "mismatch":
            return fail(422, "Idempotency-Key has already been used with a different request body")

        limited = self._rate_limited(body)
        if limited:
            return limited  # 429s are temporary, so not saved.

        result = self._book(body)
        self.idempotency.save(idempotency_key, fingerprint, result)
        return result

    def _rate_limited(self, body: Any) -> Optional[ApiResult]:
        email = body.get("email") if isinstance(body, dict) else None
        if not isinstance(email, str) or not email.strip():
            return None
        retry_after = self.rate_limiter.hit(f"email:{email.strip().lower()}")
        if retry_after is None:
            return None
        return fail(429, "too many booking attempts for this email, try again later", {"Retry-After": str(retry_after)})

    def _book(self, body: Any) -> ApiResult:
        if not isinstance(body, dict):
            return fail(400, "request body must be a JSON object")

        for field in REQUIRED_FIELDS:
            value = body.get(field)
            if value is None:
                return fail(400, f"{field} is required")
            if not isinstance(value, str):
                return fail(400, f"{field} must be a string")
            if not value.strip():
                return fail(400, f"{field} must not be empty")
        slot_id = body["slot_id"].strip()
        name = body["name"].strip()
        email = body["email"].strip().lower()

        if len(name) > MAX_NAME:
            return fail(400, f"name must be at most {MAX_NAME} characters")
        if len(email) > MAX_EMAIL or not EMAIL_RE.match(email):
            return fail(400, "email is not valid")

        slot = self.slots.get(slot_id)
        if slot is None:
            return fail(404, "slot not found")
        if slot["start_ms"] <= now_ms():
            return fail(400, "slot has already started")

        booking = {
            "id": f"b_{uuid.uuid4()}",
            "slot_id": slot["id"],
            "name": name,
            "email": email,
            "status": "confirmed",
            "created_at": iso_now(),
        }
        try:
            self.db.conn.execute(
                """INSERT INTO bookings (id, slot_id, name, email, status, created_at)
                   VALUES (:id, :slot_id, :name, :email, :status, :created_at)""",
                booking,
            )
        except sqlite3.IntegrityError as err:
            if "UNIQUE" in str(err):
                return fail(409, "slot is already booked")
            raise
        return ok(booking, 201)

    def get(self, booking_id: str) -> ApiResult:
        row = self.db.conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
        return ok(booking_dict(row)) if row else fail(404, "booking not found")

    def cancel(self, booking_id: str) -> ApiResult:
        row = self.db.conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
        if row is None:
            return fail(404, "booking not found")
        cur = self.db.conn.execute("UPDATE bookings SET status = 'cancelled' WHERE id = ? AND status = 'confirmed'", (booking_id,))
        if cur.rowcount == 0:
            return fail(409, "booking is already cancelled")
        return ok({**booking_dict(row), "status": "cancelled"})

    def list_by_email(self, email: Optional[str], limit: Optional[str], cursor: Optional[str]) -> ApiResult:
        if email is None or not email.strip():
            return fail(400, "email is required")
        email = email.strip().lower()

        page_size = DEFAULT_PAGE_SIZE
        if limit is not None:
            page_size = int(limit) if limit.isascii() and limit.isdigit() else -1
            if not 1 <= page_size <= MAX_PAGE_SIZE:
                return fail(400, f"limit must be an integer from 1 to {MAX_PAGE_SIZE}")

        after = 0
        if cursor is not None:
            decoded = decode_cursor(cursor)
            if decoded is None:
                return fail(400, "cursor is not valid")
            after = decoded

        # One extra row tells us if there's a next page.
        rows = self.db.conn.execute(
            "SELECT * FROM bookings WHERE email = ? AND seq > ? ORDER BY seq LIMIT ?", (email, after, page_size + 1)
        ).fetchall()
        page = rows[:page_size]
        next_cursor = encode_cursor(page[-1]["seq"]) if len(rows) > page_size else None
        return ok({"bookings": [booking_dict(r) for r in page], "next_cursor": next_cursor})
