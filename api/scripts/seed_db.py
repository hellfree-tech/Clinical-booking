"""Writes dummy slots + bookings straight into the local SQLite file (wipes existing data).

Usage: python scripts/seed_db.py
"""
import os
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.database import Database  # noqa: E402
from app.server import _load_dotenv  # noqa: E402

_load_dotenv()
db_path = os.environ.get("DB_PATH", "./data/clinic.db")
db = Database(db_path)

providers = ["Dr Ade", "Dr Bello", "Dr Chen"]
now = datetime.now(timezone.utc)
today = now.replace(hour=0, minute=0, second=0, microsecond=0)


def weekdays(step, n):
    days, d = [], today
    while len(days) < n:
        d += timedelta(days=step)
        if d.weekday() < 5:
            days.append(d)
    return days


iso = lambda d: d.isoformat(timespec="milliseconds").replace("+00:00", "Z")
slots = []
for day in sorted(weekdays(-1, 5) + weekdays(1, 10)):
    for provider in providers:
        for m in range(9 * 60, 17 * 60, 30):
            if 12 * 60 <= m < 13 * 60:
                continue
            start = day + timedelta(minutes=m)
            sid = f"{provider.split()[1].lower()}-{start:%Y%m%dT%H%M}"
            slots.append({"id": sid, "provider": provider, "start": iso(start), "end": iso(start + timedelta(minutes=30)),
                          "start_ms": int(start.timestamp() * 1000)})

patients = [("Ada Obi", "ada@example.com", 23), ("Tunde Bakare", "tunde@example.com", 6), ("Grace Hopper", "grace@example.com", 4),
            ("Chen Wei", "chen.wei@example.com", 3), ("Fatima Yusuf", "fatima@example.com", 2), ("Liam Murphy", "liam@example.com", 1)]

rng = random.Random(42)  # same data every run
taken, bookings = set(), []
created = now - timedelta(days=20)
for name, email, count in patients:
    for _ in range(count):
        slot = rng.choice([s for s in slots if s["id"] not in taken])
        cancelled = rng.random() < 0.25
        if not cancelled:
            taken.add(slot["id"])  # cancelled slots stay bookable
        created = min(created + timedelta(minutes=rng.randint(0, 360)), now)
        bookings.append({"id": f"b_{uuid.uuid4()}", "slot_id": slot["id"], "name": name, "email": email,
                         "status": "cancelled" if cancelled else "confirmed", "created_at": iso(created)})

with db.transaction() as conn:
    conn.execute("DELETE FROM idempotency_keys")
    conn.execute("DELETE FROM bookings")
    conn.execute("DELETE FROM slots")
    conn.executemany('INSERT INTO slots (id, provider, start, "end", start_ms) VALUES (:id, :provider, :start, :end, :start_ms)', slots)
    conn.executemany("INSERT INTO bookings (id, slot_id, name, email, status, created_at) "
                     "VALUES (:id, :slot_id, :name, :email, :status, :created_at)", bookings)

cancelled = sum(b["status"] == "cancelled" for b in bookings)
print(f"Seeded {db_path}\n  slots:    {len(slots)}\n  bookings: {len(bookings)} ({cancelled} cancelled)\n\nPatients:")
for name, email, count in patients:
    print(f"  {email:<22} {count} bookings")
print(f"\nSample booking id: {next(b['id'] for b in bookings if b['status'] == 'confirmed')}")
db.close()
