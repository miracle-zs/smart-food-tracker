from datetime import date
from collections.abc import Generator
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import SessionLocal, engine, ensure_sqlite_schema
from app.models.food_item import FoodItem
from app.schemas.item import (
    ItemCreate,
    ItemResponse,
    ItemStatusUpdate,
    ItemUpdate,
    ItemSummaryLocationCount,
    ItemSummaryResponse,
    VoiceItemCreate,
    VoiceItemResponse,
    VoiceParseResult,
    VoiceWebhookCreate,
    WebhookIngestionResponse,
)
from app.services.voice_parser import VoiceParser


router = APIRouter(prefix="/api/items", tags=["items"])
voice_parser = VoiceParser()


Base.metadata.create_all(bind=engine)
ensure_sqlite_schema(engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def to_item_response(item: FoodItem) -> ItemResponse:
    days_left = (item.expiry_date - date.today()).days
    if days_left <= 3:
        urgency = "critical"
    elif days_left <= 7:
        urgency = "warning"
    else:
        urgency = "safe"
    if days_left < 0:
        urgency = "expired"

    return ItemResponse(
        id=item.id,
        name=item.name,
        location=item.location,
        entry_date=item.entry_date,
        expiry_date=item.expiry_date,
        status=item.status,
        needs_confirmation=item.needs_confirmation,
        last_notified_stage=item.last_notified_stage,
        days_left=days_left,
        urgency=urgency,
    )


def _normalize_webhook_text(value: object) -> str | None:
    if isinstance(value, str):
        text = value.strip()
        return text or None
    if isinstance(value, dict):
        for key in ("text", "raw_text", "query", "content", "message"):
            normalized = _normalize_webhook_text(value.get(key))
            if normalized:
                return normalized
        return None
    if isinstance(value, list):
        for entry in value:
            if isinstance(entry, (dict, list)):
                normalized = _normalize_webhook_text(entry)
                if normalized:
                    return normalized
        for entry in value:
            normalized = _normalize_webhook_text(entry)
            if normalized:
                return normalized
    return None


def _extract_webhook_text(payload: VoiceWebhookCreate) -> str:
    for key in ("text", "raw_text", "query", "content", "message"):
        normalized = _normalize_webhook_text(getattr(payload, key, None))
        if normalized:
            return normalized

    extra = getattr(payload, "model_extra", None) or {}
    for key in ("text", "raw_text", "query", "content", "message"):
        if key in extra:
            normalized = _normalize_webhook_text(extra[key])
            if normalized:
                return normalized

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Webhook payload must include text content",
    )


def _persist_voice_item(raw_text: str, db: Session) -> VoiceItemResponse:
    parsed = voice_parser.parse(raw_text)
    item = FoodItem(
        name=parsed.name,
        location=parsed.location,
        expiry_date=parsed.expiry_date,
        status="active",
        needs_confirmation=parsed.needs_confirmation,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return VoiceItemResponse(
        parsed_data=VoiceParseResult(
            name=parsed.name,
            location=parsed.location,
            expiry_date=parsed.expiry_date,
            needs_confirmation=parsed.needs_confirmation,
        ),
        item=to_item_response(item),
    )


@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(payload: ItemCreate, db: Session = Depends(get_db)) -> ItemResponse:
    item = FoodItem(
        name=payload.name,
        location=payload.location,
        expiry_date=payload.expiry_date,
        status="active",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return to_item_response(item)


@router.get("", response_model=list[ItemResponse])
def list_items(
    status: str | None = Query(default=None),
    location: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[FoodItem]:
    statement = select(FoodItem)
    if status:
        statement = statement.where(FoodItem.status == status)
    if location:
        statement = statement.where(FoodItem.location == location)
    statement = statement.order_by(FoodItem.expiry_date.asc(), FoodItem.id.asc())
    return [to_item_response(item) for item in db.scalars(statement)]


@router.get("/summary", response_model=ItemSummaryResponse)
def get_item_summary(db: Session = Depends(get_db)) -> ItemSummaryResponse:
    items = list(db.scalars(select(FoodItem).order_by(FoodItem.id.asc())))

    total_count = len(items)
    pending_confirmation_count = 0
    expired_count = 0
    due_within_3_days_count = 0
    due_within_7_days_count = 0
    active_locations: Counter[str] = Counter()

    for item in items:
        days_left = (item.expiry_date - date.today()).days
        if item.needs_confirmation:
            pending_confirmation_count += 1
        if days_left < 0:
            expired_count += 1
        if 0 <= days_left <= 3:
            due_within_3_days_count += 1
        if 0 <= days_left <= 7:
            due_within_7_days_count += 1
        if item.status == "active":
            active_locations[item.location] += 1

    location_counts = [
        ItemSummaryLocationCount(location=location, count=count)
        for location, count in sorted(active_locations.items(), key=lambda entry: entry[0])
    ]

    return ItemSummaryResponse(
        total_count=total_count,
        pending_confirmation_count=pending_confirmation_count,
        expired_count=expired_count,
        due_within_3_days_count=due_within_3_days_count,
        due_within_7_days_count=due_within_7_days_count,
        distinct_location_count=len(active_locations),
        location_counts=location_counts,
    )


@router.post("/voice", response_model=VoiceItemResponse, status_code=status.HTTP_201_CREATED)
def create_item_from_voice(
    payload: VoiceItemCreate,
    db: Session = Depends(get_db),
) -> VoiceItemResponse:
    return _persist_voice_item(payload.raw_text, db)


@router.post("/voice/webhook", response_model=WebhookIngestionResponse, status_code=status.HTTP_201_CREATED)
def create_item_from_voice_webhook(
    payload: VoiceWebhookCreate,
    db: Session = Depends(get_db),
) -> WebhookIngestionResponse:
    result = _persist_voice_item(_extract_webhook_text(payload), db)
    return WebhookIngestionResponse(ok=True, item_id=result.item.id)


@router.put("/{item_id}/status", response_model=ItemResponse)
def update_item_status(
    item_id: int,
    payload: ItemStatusUpdate,
    db: Session = Depends(get_db),
) -> FoodItem:
    item = db.get(FoodItem, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    item.status = payload.status
    db.commit()
    db.refresh(item)
    return to_item_response(item)


@router.put("/{item_id}", response_model=ItemResponse)
def update_item(
    item_id: int,
    payload: ItemUpdate,
    db: Session = Depends(get_db),
) -> FoodItem:
    item = db.get(FoodItem, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    if item.status != "active":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only active items can be edited")
    if not item.needs_confirmation:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only pending active items can be edited",
        )

    item.name = payload.name
    item.location = payload.location
    item.expiry_date = payload.expiry_date
    db.commit()
    db.refresh(item)
    return to_item_response(item)


@router.post("/{item_id}/confirm", response_model=ItemResponse)
def confirm_item(
    item_id: int,
    db: Session = Depends(get_db),
) -> FoodItem:
    item = db.get(FoodItem, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    if item.status != "active":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only active items can be confirmed")
    if not item.needs_confirmation:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only pending active items can be confirmed",
        )

    item.needs_confirmation = False
    db.commit()
    db.refresh(item)
    return to_item_response(item)
