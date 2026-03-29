from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from database import User, get_db
from timeline import service
from timeline.schemas import TimelineEventCreate, TimelineEventUpdate

router = APIRouter()


@router.get("/timeline/events")
def list_events(
    year: Optional[int] = Query(None),
    tag: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return service.get_events(db, year, tag)


@router.post("/timeline/events")
def create_event(
    body: TimelineEventCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return service.create_event(db, body)


@router.put("/timeline/events/{event_id}")
def update_event(
    event_id: str,
    body: TimelineEventUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    service.update_event(db, event_id, body)
    return {"ok": True}


@router.delete("/timeline/events/{event_id}")
def delete_event(
    event_id: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    service.delete_event(db, event_id)
    return {"ok": True}
