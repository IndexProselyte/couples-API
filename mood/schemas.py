from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

MoodValue = Literal["happy", "in_love", "sad", "tired", "excited", "neutral"]


class MoodItem(BaseModel):
    value: str


class MoodResponse(BaseModel):
    your_mood: MoodItem
    partner_mood: MoodItem


class MoodUpdate(BaseModel):
    mood: MoodValue
