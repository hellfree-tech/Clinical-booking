"""Loads demo data when the database is empty, e.g. after a free Render instance restarts."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from .database import Database

logger = logging.getLogger("demo_seed")

PROVIDERS = ["Dr Ade", "Dr Bello", "Dr Chen"]
PATIENTS = [
    ("Ada Obi", "ada@example.com", 12),
    ("Tunde Bakare", "tunde@example.com", 5),
    ("Grace Hopper", "grace@example.com", 3),
    ("Chen Wei", "chen.wei@example.com", 2),
]


def _iso(dt: datetime) -> str:
    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def build_slots() -> List[Dict[str, str]]:
    """10 upcoming weekdays, 09:00–16:30 every 30 min, lunch off."""
    slots = []
    day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    added = 0
    while added < 10:
        day += timedelta(days=1)
        if day.weekday() >= 5:
            continue
        added += 1
        for provider in PROVIDERS:
            for m in range(9 * 60, 17 * 60, 30):
                if 12 * 60 <= m < 13 * 60:
                    continue
                start = day + timedelta(minutes=m)
                slot_id = f"{provider.split()[1].lower()}-{start.strftime('%Y%m%dT%H%M')}"
                slots.append({"id": slot_id, "provider": provider, "start": _iso(start), "end": _iso(start + timedelta(minutes=30))})
    return slots


def seed_if_empty(db: Database) -> None:
    if db.conn.execute("SELECT COUNT(*) FROM slots").fetchone()[0] > 0:
        return

    slots = build_slots()
    created_at = datetime.now(timezone.utc) - timedelta(days=1)
    count = 0
    with db.transaction() as conn:
        conn.executemany(
            'INSERT INTO slots (id, provider, start, "end", start_ms) VALUES (?, ?, ?, ?, ?)',
            [
                (s["id"], s["provider"], s["start"], s["end"], int(datetime.fromisoformat(s["start"].replace("Z", "+00:00")).timestamp() * 1000))
                for s in slots
            ],
        )
        i = 0
        for name, email, n_bookings in PATIENTS:
            for n in range(n_bookings):
                slot = slots[(i * 7) % len(slots)]
                status = "cancelled" if n % 4 == 3 else "confirmed"
                conn.execute(
                    "INSERT INTO bookings (id, slot_id, name, email, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (f"b_{uuid.uuid4()}", slot["id"], name, email, status, _iso(created_at + timedelta(minutes=i))),
                )
                i += 1
                count += 1
    logger.info("Empty database: seeded %d slots and %d bookings", len(slots), count)
