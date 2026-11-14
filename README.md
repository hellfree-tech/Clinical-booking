# Clinic Booking 

The clinic booking app, built with a **FastAPI** backend and designed with **React** frontend.

- **API:** FastAPI + SQLite, in [`api/`](api/). It has the endpoints, rules and error format.
- **Web app:** React + Vite, in [`frontend/`](frontend/). It has a indigo-to-violet theme, colour-coded doctors and a step indicator

## Links

| | Local |
| --- | --- |
| Web app | http://localhost:5174 |
| API docs (Swagger) | http://localhost:8000/docs |
| API docs (ReDoc) | http://localhost:8000/redoc |

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


Both versions use the same database rule (a partial unique index) to stop double-booking. **Recommended before real production use:** move to PostgreSQL (or MySQL or MongoDB) so several servers can share the data, keep the rate-limit counts and idempotency keys in Redis, and add automated tests.
