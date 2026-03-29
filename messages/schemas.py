from __future__ import annotations

from typing import Any, List, Literal, Optional

from pydantic import BaseModel


class MessageResponse(BaseModel):
    id: str
    text: str
    is_sent: bool
    time: str                        # "HH:mm" UTC
    date: Optional[str] = None       # "YYYY-MM-DD" — only on first msg of each day
    is_file: bool
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    image_url: Optional[str] = None
    sticker_path: Optional[str] = None
    reactions: List[str]
    is_starred: bool
    is_voice: bool
    voice_duration_ms: Optional[int] = None
    voice_waveform: Optional[Any] = None
    reply_to_text: Optional[str] = None
    reply_to_is_sent: Optional[bool] = None


class MessagesResponse(BaseModel):
    messages: List[MessageResponse]


class MessageCreate(BaseModel):
    text: str
    reply_to_id: Optional[str] = None
    reply_to_text: Optional[str] = None
    # Client sends this from its own perspective; ignored on write —
    # we derive reply_to_is_sent from reply_to_sender_id stored server-side.
    reply_to_is_sent: Optional[bool] = None


class ReactionUpdate(BaseModel):
    emoji: str
    action: Literal["add", "remove"]


class StarUpdate(BaseModel):
    starred: bool
