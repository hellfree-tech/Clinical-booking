from __future__ import annotations

import math
import time
from typing import Dict, List, Optional


def now_ms() -> int:
    return int(time.time() * 1000)


class RateLimiter:
    """Level 5: sliding-window limit per key. In-memory, so single-instance only."""

    def __init__(self, max_hits: int, window_ms: int):
        self.max_hits = max_hits
        self.window_ms = window_ms
        self._hits: Dict[str, List[int]] = {}
        self._last_sweep = now_ms()

    def hit(self, key: str, now: Optional[int] = None) -> Optional[int]:
        """Records an attempt. Returns None if allowed, else seconds until retry."""
        now = now_ms() if now is None else now
        self._sweep(now)
        window_start = now - self.window_ms
        recent = [t for t in self._hits.get(key, []) if t > window_start]
        if len(recent) >= self.max_hits:
            self._hits[key] = recent
            return max(1, math.ceil((recent[0] - window_start) / 1000))
        recent.append(now)
        self._hits[key] = recent
        return None

    def clear(self) -> None:
        self._hits.clear()

    def _sweep(self, now: int) -> None:
        if now - self._last_sweep < self.window_ms:
            return
        self._last_sweep = now
        stale = [k for k, times in self._hits.items() if times[-1] <= now - self.window_ms]
        for k in stale:
            del self._hits[k]
