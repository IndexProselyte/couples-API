from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel


class TimelineEventResponse(BaseModel):
    id: str
    title: str
    date: int                        # epoch milliseconds
    canvas: List[Any]
    stickers: List[Any]
    tags: List[str]
    location: Optional[str] = None
    dot_color: Optional[int] = None
    line_color: Optional[int] = None
    card_color: Optional[int] = None
    is_pinned: bool


class TimelineEventsResponse(BaseModel):
    events: List[TimelineEventResponse]


class TimelineEventCreate(BaseModel):
    title: str
    date: int                        # epoch milliseconds
    canvas: List[Any] = []
    stickers: List[Any] = []
    tags: List[str] = []
    location: Optional[str] = None
    dot_color: Optional[int] = None
    line_color: Optional[int] = None
    card_color: Optional[int] = None
    is_pinned: bool = False


class TimelineEventUpdate(TimelineEventCreate):
    pass


class TimelineCreateResponse(BaseModel):
    id: str


class TimelinePinUpdate(BaseModel):
    is_pinned: bool
