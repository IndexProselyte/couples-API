from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from database import TimelineEvent
from timeline.schemas import (
    TimelineEventCreate,
    TimelineEventResponse,
    TimelineEventUpdate,
)


def get_events(
    db: Session, year: int | None, tag: str | None
) -> dict:
    events = (
        db.query(TimelineEvent).order_by(TimelineEvent.event_date.asc()).all()
    )

    result: list[TimelineEventResponse] = []
    for e in events:
        if year is not None:
            event_year = datetime.fromtimestamp(
                e.event_date / 1000, tz=timezone.utc
            ).year
            if event_year != year:
                continue
        if tag is not None and tag not in (e.tags or []):
            continue
        result.append(_to_response(e))

    return {"events": [r.model_dump() for r in result]}


def create_event(db: Session, body: TimelineEventCreate) -> tuple[dict, TimelineEventResponse]:
    event = TimelineEvent(
        id=str(uuid.uuid4()),
        title=body.title,
        event_date=body.date,
        canvas=body.canvas,
        stickers=body.stickers,
        tags=body.tags,
        location=body.location,
        dot_color=body.dot_color,
        line_color=body.line_color,
        card_color=body.card_color,
        is_pinned=body.is_pinned,
    )
    db.add(event)
    db.commit()
    return {"id": event.id}, _to_response(event)


def update_event(
    db: Session, event_id: str, body: TimelineEventUpdate
) -> TimelineEventResponse:
    event = db.query(TimelineEvent).filter(TimelineEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    event.title = body.title
    event.event_date = body.date
    event.canvas = body.canvas
    event.stickers = body.stickers
    event.tags = body.tags
    event.location = body.location
    event.dot_color = body.dot_color
    event.line_color = body.line_color
    event.card_color = body.card_color
    event.is_pinned = body.is_pinned

    # Explicitly mark JSON columns as modified so SQLAlchemy flushes them.
    flag_modified(event, "canvas")
    flag_modified(event, "stickers")
    flag_modified(event, "tags")
    db.commit()
    return _to_response(event)


def pin_event(db: Session, event_id: str, is_pinned: bool) -> None:
    event = db.query(TimelineEvent).filter(TimelineEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    event.is_pinned = is_pinned
    db.commit()


def delete_event(db: Session, event_id: str) -> None:
    event = db.query(TimelineEvent).filter(TimelineEvent.id == event_id).first()
    if event:
        db.delete(event)
        db.commit()


# ── Internal ──────────────────────────────────────────────────────────────────


def _to_response(event: TimelineEvent) -> TimelineEventResponse:
    return TimelineEventResponse(
        id=event.id,
        title=event.title,
        date=event.event_date,          # exposed as "date" per the API contract
        canvas=event.canvas or [],
        stickers=event.stickers or [],
        tags=event.tags or [],
        location=event.location,
        dot_color=event.dot_color,
        line_color=event.line_color,
        card_color=event.card_color,
        is_pinned=bool(event.is_pinned),
    )
