from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class ApiResult:
    """Returned (not raised) so responses can be replayed for idempotency."""

    status: int
    body: Any
    headers: Dict[str, str] = field(default_factory=dict)


def ok(body: Any, status: int = 200) -> ApiResult:
    return ApiResult(status, body)


def fail(status: int, error: str, headers: Dict[str, str] | None = None) -> ApiResult:
    return ApiResult(status, {"error": error}, headers or {})


class ApiError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message
