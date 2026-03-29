from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class UserInfo(BaseModel):
    id: str
    role: str


class MoodInfo(BaseModel):
    value: str


class StatsResponse(BaseModel):
    users: list[UserInfo]
    messages: int
    timeline_events: int
    hers_mood: MoodInfo
    his_mood: MoodInfo


class ResetPasswordRequest(BaseModel):
    password: str = Field(min_length=8)


class DeleteDataRequest(BaseModel):
    type: Literal["chat", "timeline", "all"]


class DeleteDataResponse(BaseModel):
    ok: bool
    deleted: int
