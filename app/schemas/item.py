from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class ItemCreate(BaseModel):
    name: str
    location: str
    expiry_date: date


class ItemUpdate(ItemCreate):
    pass


class VoiceItemCreate(BaseModel):
    raw_text: str


class VoiceWebhookCreate(BaseModel):
    model_config = ConfigDict(extra="allow")

    text: Any = None
    raw_text: Any = None
    query: Any = None
    content: Any = None
    message: Any = None


class ItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    location: str
    entry_date: datetime
    expiry_date: date
    status: str
    needs_confirmation: bool
    last_notified_stage: str | None = None
    days_left: int
    urgency: str


class ItemSummaryLocationCount(BaseModel):
    location: str
    count: int


class ItemSummaryResponse(BaseModel):
    total_count: int
    pending_confirmation_count: int
    expired_count: int
    due_within_3_days_count: int
    due_within_7_days_count: int
    distinct_location_count: int
    location_counts: list[ItemSummaryLocationCount]


class ItemStatusUpdate(BaseModel):
    status: Literal["consumed", "discarded"]


class VoiceParseResult(BaseModel):
    name: str
    location: str
    expiry_date: date
    needs_confirmation: bool


class VoiceItemResponse(BaseModel):
    parsed_data: VoiceParseResult
    item: ItemResponse


class WebhookIngestionResponse(BaseModel):
    ok: bool
    item_id: int
