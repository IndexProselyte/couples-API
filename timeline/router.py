from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from database import User, get_db
from timeline import service
from timeline.schemas import TimelineCreateResponse, TimelineEventCreate, TimelineEventsResponse, TimelineEventUpdate, TimelinePinUpdate
from ws.manager import manager

router = APIRouter()


@router.get("/timeline/events", response_model=TimelineEventsResponse)
def list_events(
    year: Optional[int] = Query(None),
    tag: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return service.get_events(db, year, tag)


@router.post("/timeline/events", response_model=TimelineCreateResponse)
async def create_event(
    body: TimelineEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    id_response, full_event = service.create_event(db, body)
    await manager.broadcast(
        {"type": "timeline_event_create", "data": full_event.model_dump()},
        exclude_user_id=current_user.id,
    )
    return id_response


@router.put("/timeline/events/{event_id}")
async def update_event(
    event_id: str,
    body: TimelineEventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated = service.update_event(db, event_id, body)
    await manager.broadcast(
        {"type": "timeline_event_update", "data": updated.model_dump()},
        exclude_user_id=current_user.id,
    )
    return {"ok": True}


@router.put("/timeline/events/{event_id}/pin")
async def pin_event(
    event_id: str,
    body: TimelinePinUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service.pin_event(db, event_id, body.is_pinned)
    await manager.broadcast(
        {"type": "timeline_event_pin", "data": {"id": event_id, "is_pinned": body.is_pinned}},
        exclude_user_id=current_user.id,
    )
    return {"ok": True}


@router.delete("/timeline/events/{event_id}")
async def delete_event(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service.delete_event(db, event_id)
    await manager.broadcast(
        {"type": "timeline_event_delete", "data": {"id": event_id}},
        exclude_user_id=current_user.id,
    )
    return {"ok": True}
