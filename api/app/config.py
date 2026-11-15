from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Mapping, Union


@dataclass(frozen=True)
class Config:
    api_key: str
    port: int
    db_path: str
    cors_origins: Union[List[str], str]  # "*" or an allow-list
    rate_limit_max: int
    rate_limit_window_ms: int
    idempotency_ttl_ms: int
    log_requests: bool
    seed_on_start: bool = False


def _positive_int(env: Mapping[str, str], name: str, default: int) -> int:
    raw = env.get(name, "")
    if raw == "":
        return default
    if not (raw.isascii() and raw.isdigit()) or int(raw) < 1:
        raise ValueError(f'{name} must be a positive integer, got "{raw}"')
    return int(raw)


def load_config(env: Mapping[str, str] = os.environ) -> Config:
    api_key = env.get("API_KEY", "").strip()
    if not api_key:
        raise ValueError("API_KEY environment variable is required")

    origins = [o.strip() for o in env.get("CORS_ORIGIN", "*").split(",") if o.strip()]
    return Config(
        api_key=api_key,
        port=_positive_int(env, "PORT", 8000),
        db_path=env.get("DB_PATH", "./data/clinic.db"),
        cors_origins="*" if not origins or "*" in origins else origins,
        rate_limit_max=_positive_int(env, "RATE_LIMIT_MAX", 5),
        rate_limit_window_ms=_positive_int(env, "RATE_LIMIT_WINDOW_MS", 60_000),
        idempotency_ttl_ms=_positive_int(env, "IDEMPOTENCY_TTL_MS", 24 * 60 * 60 * 1000),
        log_requests=env.get("APP_ENV") != "test",
        seed_on_start=env.get("SEED_ON_START") == "true",
    )
