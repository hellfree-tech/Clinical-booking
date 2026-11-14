"""Loads 7 weekdays of demo slots through POST /reset (wipes all bookings).

Usage: API_URL=https://your-api python scripts/seed.py   (API_KEY from env or .env)
"""
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.server import _load_dotenv  # noqa: E402

_load_dotenv()
API_URL = os.environ.get("API_URL", "http://localhost:8000").rstrip("/")
API_KEY = os.environ.get("API_KEY") or sys.exit("Set API_KEY")

providers = ["Dr Ade", "Dr Bello", "Dr Chen"]
slots = []
day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
added = 0
while added < 7:
    day += timedelta(days=1)
    if day.weekday() >= 5:
        continue
    added += 1
    for p, provider in enumerate(providers):
        for h in range(9, 17):
            if h == 12 or (h + p) % 3 == 0:
                continue
            start = day.replace(hour=h)
            end = start + timedelta(minutes=30)
            iso = lambda d: d.isoformat().replace("+00:00", "Z")
            slots.append({"id": f"{start:%Y-%m-%dT%H}-{p}", "provider": provider, "start": iso(start), "end": iso(end)})

print(f"Seeding {len(slots)} slots → {API_URL}")
req = urllib.request.Request(
    f"{API_URL}/reset",
    data=json.dumps({"slots": slots}).encode(),
    headers={"Content-Type": "application/json", "X-API-Key": API_KEY},
    method="POST",
)
try:
    with urllib.request.urlopen(req, timeout=60) as res:
        print(res.status, res.read().decode())
except urllib.error.HTTPError as err:
    print(err.code, err.read().decode())
    if err.code == 401:
        print("The API key does not match the one set on the server.")
    sys.exit(1)
except urllib.error.URLError as err:
    sys.exit(f"Could not reach {API_URL} ({err.reason}). Set API_URL, e.g. API_URL=https://your-service.onrender.com")
