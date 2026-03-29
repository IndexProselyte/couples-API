from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class CoupleProfileResponse(BaseModel):
    start_date: str
    your_name: str
    partner_name: str
    couple_photo_url: Optional[str] = None
    partner_avatar_url: Optional[str] = None


class CoupleProfileUpdate(BaseModel):
    start_date: Optional[str] = None
    your_name: Optional[str] = None
    partner_name: Optional[str] = None
