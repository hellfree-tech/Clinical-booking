from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from typing import Iterator

SCHEMA = """
CREATE TABLE IF NOT EXISTS slots (
  id        TEXT PRIMARY KEY,
  provider  TEXT NOT NULL,
  start     TEXT NOT NULL,
  "end"     TEXT NOT NULL,
  start_ms  INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS slots_by_start ON slots (start_ms, id);
CREATE INDEX IF NOT EXISTS slots_by_provider ON slots (provider, start_ms, id);

CREATE TABLE IF NOT EXISTS bookings (
  seq        INTEGER PRIMARY KEY AUTOINCREMENT,
  id         TEXT NOT NULL UNIQUE,
  slot_id    TEXT NOT NULL REFERENCES slots (id) ON DELETE CASCADE,
  name       TEXT NOT NULL,
  email      TEXT NOT NULL,
  status     TEXT NOT NULL CHECK (status IN ('confirmed', 'cancelled')),
  created_at TEXT NOT NULL
);
-- Level 3: one confirmed booking per slot.
CREATE UNIQUE INDEX IF NOT EXISTS one_confirmed_booking_per_slot
  ON bookings (slot_id) WHERE status = 'confirmed';
CREATE INDEX IF NOT EXISTS bookings_by_email ON bookings (email, seq);

CREATE TABLE IF NOT EXISTS idempotency_keys (
  key         TEXT PRIMARY KEY,
  fingerprint TEXT NOT NULL,
  status      INTEGER NOT NULL,
  body        TEXT NOT NULL,
  created_at  INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idempotency_by_created ON idempotency_keys (created_at);
"""


class Database:
    def __init__(self, path: str):
        if path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        # Autocommit mode; multi-statement writes use transaction().
        self.conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self.conn.row_factory = sqlite3.Row
        for pragma in ("journal_mode = WAL", "synchronous = NORMAL", "busy_timeout = 5000", "foreign_keys = ON"):
            self.conn.execute(f"PRAGMA {pragma}")
        self.conn.executescript(SCHEMA)

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            yield self.conn
            self.conn.execute("COMMIT")
        except BaseException:
            self.conn.execute("ROLLBACK")
            raise

    def close(self) -> None:
        self.conn.close()
