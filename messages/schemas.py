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
    text: str = ""

    # ── Reply context ─────────────────────────────────────────────────────────
    reply_to_id: Optional[str] = None
    reply_to_text: Optional[str] = None
    # Client sends this from its own perspective; ignored on write —
    # we derive reply_to_is_sent from reply_to_sender_id stored server-side.
    reply_to_is_sent: Optional[bool] = None

    # ── Image ─────────────────────────────────────────────────────────────────
    # Workflow: POST /upload → receive URL → POST /messages with image_url set.
    image_url: Optional[str] = None

    # ── File attachment ───────────────────────────────────────────────────────
    # Workflow: POST /upload → receive URL → POST /messages with is_file=True,
    # image_url set to the download URL, and file_name / file_size filled in.
    is_file: bool = False
    file_name: Optional[str] = None
    file_size: Optional[int] = None

    # ── Sticker ───────────────────────────────────────────────────────────────
    # No upload needed — sticker_path is a Flutter asset reference bundled in
    # the app (e.g. "assets/stickers/hamster/0-1.thumb128.png").
    sticker_path: Optional[str] = None

    # ── Voice note ────────────────────────────────────────────────────────────
    # Workflow: POST /upload → receive URL → POST /messages with is_voice=True,
    # image_url set to the audio URL, and voice_duration_ms / voice_waveform set.
    is_voice: bool = False
    voice_duration_ms: Optional[int] = None
    voice_waveform: Optional[Any] = None


class ReactionUpdate(BaseModel):
    emoji: str
    action: Literal["add", "remove"]


class StarUpdate(BaseModel):
    starred: bool
