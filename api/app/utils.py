from __future__ import annotations

import base64
import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
MAX_NAME = 200
MAX_EMAIL = 254
MAX_IDEMPOTENCY_KEY = 255
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 50
REQUIRED_FIELDS = ("slot_id", "name", "email")


def parse_iso_ms(value: str) -> Optional[int]:
    """ISO 8601 → epoch ms (naive times are treated as UTC). None if invalid."""
    try:
        dt = datetime.fromisoformat(value.strip().replace("Z", "+00:00").replace("z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def booking_dict(row: Any) -> Dict[str, Any]:
    return {k: row[k] for k in ("id", "slot_id", "name", "email", "status", "created_at")}


def encode_cursor(seq: int) -> str:
    return base64.urlsafe_b64encode(json.dumps({"after": seq}).encode()).decode().rstrip("=")


def decode_cursor(cursor: str) -> Optional[int]:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        after = json.loads(base64.urlsafe_b64decode(padded.encode()))["after"]
    except Exception:
        return None
    return after if isinstance(after, int) and not isinstance(after, bool) and after >= 0 else None
