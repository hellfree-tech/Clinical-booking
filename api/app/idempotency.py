from __future__ import annotations

import hashlib
import json
from typing import Any, Optional, Tuple

from .database import Database
from .errors import ApiResult
from .rate_limiter import now_ms


class IdempotencyStore:
    """Level 4: stores one response per Idempotency-Key; expired rows are ignored and swept."""

    def __init__(self, db: Database, ttl_ms: int):
        self.db = db
        self.ttl_ms = ttl_ms
        self._last_purge = now_ms()

    @staticmethod
    def fingerprint(body: Any) -> str:
        # sort_keys: key order doesn't affect the fingerprint.
        canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def lookup(self, key: str, fingerprint: str, now: Optional[int] = None) -> Tuple[str, Optional[ApiResult]]:
        """Returns ("new", None), ("mismatch", None) or ("replay", result)."""
        now = now_ms() if now is None else now
        self._maybe_purge(now)
        row = self.db.conn.execute(
            "SELECT fingerprint, status, body FROM idempotency_keys WHERE key = ? AND created_at >= ?",
            (key, now - self.ttl_ms),
        ).fetchone()
        if row is None:
            return "new", None
        if row["fingerprint"] != fingerprint:
            return "mismatch", None
        return "replay", ApiResult(row["status"], json.loads(row["body"]))

    def save(self, key: str, fingerprint: str, result: ApiResult, now: Optional[int] = None) -> None:
        # REPLACE overwrites an expired row not yet swept.
        self.db.conn.execute(
            "INSERT OR REPLACE INTO idempotency_keys (key, fingerprint, status, body, created_at) VALUES (?, ?, ?, ?, ?)",
            (key, fingerprint, result.status, json.dumps(result.body), now_ms() if now is None else now),
        )

    def _maybe_purge(self, now: int) -> None:
        if now - self._last_purge < min(self.ttl_ms, 60 * 60 * 1000):
            return
        self._last_purge = now
        self.db.conn.execute("DELETE FROM idempotency_keys WHERE created_at < ?", (now - self.ttl_ms,))
