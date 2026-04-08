from datetime import date
from collections.abc import Generator

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
    VoiceItemCreate,
    VoiceItemResponse,
    VoiceParseResult,
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


@router.post("/voice", response_model=VoiceItemResponse, status_code=status.HTTP_201_CREATED)
def create_item_from_voice(
    payload: VoiceItemCreate,
    db: Session = Depends(get_db),
) -> VoiceItemResponse:
    parsed = voice_parser.parse(payload.raw_text)
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
