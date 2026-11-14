from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class Slot(BaseModel):
    id: str = Field(examples=["s1"])
    provider: str = Field(examples=["Dr Ade"])
    start: str = Field(json_schema_extra={"format": "date-time"}, examples=["2026-12-10T09:00:00Z"])
    end: str = Field(json_schema_extra={"format": "date-time"}, examples=["2026-12-10T09:30:00Z"])


class SlotWithAvailability(Slot):
    available: bool = Field(description="false while the slot has a confirmed booking")


class SlotList(BaseModel):
    slots: List[SlotWithAvailability]


class Booking(BaseModel):
    id: str = Field(examples=["b_3f1c2a9e-6f0b-4c1e-9d8a-2b7e5c4d1a00"])
    slot_id: str = Field(examples=["s1"])
    name: str = Field(examples=["Ada Obi"])
    email: str = Field(examples=["ada@example.com"])
    status: Literal["confirmed", "cancelled"]
    created_at: str = Field(json_schema_extra={"format": "date-time"})


class BookingPage(BaseModel):
    bookings: List[Booking]
    next_cursor: Optional[str] = Field(description="Pass back as `cursor` for the next page; null on the last page")


class ErrorOut(BaseModel):
    error: str = Field(examples=["slot not found"])


class ResetOut(BaseModel):
    ok: bool
    slots: int


# Request bodies are read manually (to control validation order), so they're documented inline.
_SLOT_SCHEMA = {
    "type": "object",
    "required": ["id", "provider", "start", "end"],
    "properties": {
        "id": {"type": "string", "example": "s1"},
        "provider": {"type": "string", "example": "Dr Ade"},
        "start": {"type": "string", "format": "date-time", "example": "2026-12-10T09:00:00Z"},
        "end": {"type": "string", "format": "date-time", "example": "2026-12-10T09:30:00Z"},
    },
}
NEW_BOOKING_BODY = {
    "required": True,
    "content": {
        "application/json": {
            "schema": {
                "type": "object",
                "required": ["slot_id", "name", "email"],
                "properties": {
                    "slot_id": {"type": "string", "example": "s1"},
                    "name": {"type": "string", "example": "Ada Obi"},
                    "email": {"type": "string", "example": "ada@example.com"},
                },
            }
        }
    },
}
RESET_BODY = {
    "required": True,
    "content": {
        "application/json": {
            "schema": {"type": "object", "required": ["slots"], "properties": {"slots": {"type": "array", "items": _SLOT_SCHEMA}}}
        }
    },
}


def errors(*codes_and_descriptions):
    return {code: {"model": ErrorOut, "description": desc} for code, desc in codes_and_descriptions}
