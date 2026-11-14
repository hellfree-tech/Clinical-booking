from __future__ import annotations

from typing import Any, Dict, List, Optional

from .database import Database
from .errors import ApiError
from .utils import parse_iso_ms

SLOT_FIELDS = ("id", "provider", "start", "end")


class SlotsService:
    def __init__(self, db: Database):
        self.db = db

    def list(self, provider: Optional[str] = None) -> List[Dict[str, Any]]:
        rows = self.db.conn.execute(
            """SELECT s.id, s.provider, s.start, s."end",
                      EXISTS (SELECT 1 FROM bookings b WHERE b.slot_id = s.id AND b.status = 'confirmed') AS booked
                 FROM slots s
                WHERE (:provider IS NULL OR s.provider = :provider)
                ORDER BY s.start_ms, s.id""",
            {"provider": provider},
        ).fetchall()
        return [
            {"id": r["id"], "provider": r["provider"], "start": r["start"], "end": r["end"], "available": r["booked"] == 0}
            for r in rows
        ]

    def get(self, slot_id: str):
        return self.db.conn.execute('SELECT id, provider, start, "end", start_ms FROM slots WHERE id = ?', (slot_id,)).fetchone()

    @staticmethod
    def parse_reset_body(body: Any) -> List[Dict[str, Any]]:
        slots = body.get("slots") if isinstance(body, dict) else None
        if not isinstance(slots, list):
            raise ApiError(400, "slots must be an array")

        seen = set()
        parsed = []
        for i, raw in enumerate(slots):
            if not isinstance(raw, dict):
                raise ApiError(400, f"slots[{i}] must be an object")
            for f in SLOT_FIELDS:
                if not isinstance(raw.get(f), str) or not raw[f].strip():
                    raise ApiError(400, f"slots[{i}].{f} is required")
            start_ms = parse_iso_ms(raw["start"])
            if start_ms is None:
                raise ApiError(400, f"slots[{i}].start is not a valid date-time")
            if parse_iso_ms(raw["end"]) is None:
                raise ApiError(400, f"slots[{i}].end is not a valid date-time")
            if raw["id"] in seen:
                raise ApiError(400, f"duplicate slot id: {raw['id']}")
            seen.add(raw["id"])
            parsed.append({**{f: raw[f] for f in SLOT_FIELDS}, "start_ms": start_ms})
        return parsed

    def replace_all(self, slots: List[Dict[str, Any]]) -> None:
        with self.db.transaction() as conn:
            conn.execute("DELETE FROM idempotency_keys")
            conn.execute("DELETE FROM bookings")
            conn.execute("DELETE FROM slots")
            conn.executemany(
                'INSERT INTO slots (id, provider, start, "end", start_ms) VALUES (:id, :provider, :start, :end, :start_ms)',
                slots,
            )
