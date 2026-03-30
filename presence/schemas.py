from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class PresenceUpdate(BaseModel):
    online: bool


class PresenceInfo(BaseModel):
    user_id: str
    is_online: bool
    last_seen: Optional[str] = None  # ISO 8601 UTC, null if never seen


class PresenceResponse(BaseModel):
    your: PresenceInfo
    partner: PresenceInfo
