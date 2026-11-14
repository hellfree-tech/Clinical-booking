# Clinic Booking v2

The clinic booking app, rebuilt with a **FastAPI** backend and a redesigned **React** frontend. It's a rewrite of v1 (NestJS), which lives in the separate `clinical-booking` folder.

- **API:** FastAPI + SQLite, in [`api/`](api/). It has the same endpoints, rules and error format as v1.
- **Web app:** React + Vite, in [`frontend/`](frontend/). It has a new indigo-to-violet theme, colour-coded doctors and a step indicator.

## Links

| | Local |
| --- | --- |
| Web app | http://localhost:5174 |
| API docs (Swagger) | http://localhost:8000/docs |
| API docs (ReDoc) | http://localhost:8000/redoc |

v2 uses different ports from v1 (3000 and 5173), so both versions can run side by side.

## Running it locally

You'll need Python 3.9 or newer and Node 22.9 or newer.

**1. Set the API key.** Copy the examples and put the same key in both files:

```bash
cp api/.env.example api/.env
cp frontend/.env.example frontend/.env
```

**2. Start the API** (first terminal):

```bash
cd api
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/seed_db.py   # optional: test slots and bookings
.venv/bin/python -m app.server
```

**3. Start the web app** (second terminal):

```bash
cd frontend
npm install
npm run dev
```

Then open http://localhost:5174.

## Test data

`scripts/seed_db.py` fills the local database with about 600 slots and 39 bookings. Try `ada@example.com` under **My bookings**: it has 23 bookings to page through.

To load slots into a deployed API instead, run this from `api/`:
```bash
API_URL=https://your-api.onrender.com .venv/bin/python scripts/seed.py
```

## Deploying

- **API:** create a Render **Web Service** with the Docker runtime and the root directory set to `api`. Set `API_KEY`. Keep it to a single instance, because the rate limiter keeps its counts in memory.
- **Web app:** deploy to Vercel with the root directory set to `frontend`. Set `API_URL` and `API_KEY`.

## What's different from v1

| | v1 | v2 |
| --- | --- | --- |
| Backend | NestJS (TypeScript) | FastAPI (Python) |
| Concurrency safety | Synchronous better-sqlite3 on Node's single thread | Async handlers with synchronous `sqlite3` on the event loop |
| Docs | Swagger at `/docs` | Swagger at `/docs`, plus ReDoc at `/redoc` |
| Design | Teal, minimal | Indigo-to-violet gradient, colour-coded doctors, step indicator, initials avatars |

Both versions use the same database rule (a partial unique index) to stop double-booking. **Recommended before real production use:** move to PostgreSQL (or MySQL or MongoDB) so several servers can share the data, keep the rate-limit counts and idempotency keys in Redis, and add automated tests.
