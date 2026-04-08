from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ItemCreate(BaseModel):
    name: str
    location: str
    expiry_date: date


class VoiceItemCreate(BaseModel):
    raw_text: str


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


class ItemStatusUpdate(BaseModel):
    status: str


class VoiceParseResult(BaseModel):
    name: str
    location: str
    expiry_date: date
    needs_confirmation: bool


class VoiceItemResponse(BaseModel):
    parsed_data: VoiceParseResult
    item: ItemResponse
