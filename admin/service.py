from __future__ import annotations

import bcrypt
from fastapi import HTTPException
from sqlalchemy.orm import Session

from admin.schemas import (
    DeleteDataResponse,
    MoodInfo,
    StatsResponse,
    UserInfo,
)
from database import Message, Mood, TimelineEvent, User


def get_stats(db: Session) -> StatsResponse:
    users = [
        UserInfo(id=u.id, role=u.role)
        for u in db.query(User).filter(User.role != "admin").all()
    ]

    message_count = db.query(Message).filter(Message.deleted.is_(False)).count()
    event_count = db.query(TimelineEvent).count()

    hers_user = db.query(User).filter(User.role == "hers").first()
    his_user = db.query(User).filter(User.role == "his").first()

    def _mood(user: User | None) -> MoodInfo:
        if not user:
            return MoodInfo(value="neutral")
        mood = db.query(Mood).filter(Mood.user_id == user.id).first()
        return MoodInfo(value=mood.value if mood else "neutral")

    return StatsResponse(
        users=users,
        messages=message_count,
        timeline_events=event_count,
        hers_mood=_mood(hers_user),
        his_mood=_mood(his_user),
    )


def reset_password(db: Session, role: str, new_password: str) -> None:
    if role not in ("hers", "his"):
        raise HTTPException(status_code=400, detail="Role must be 'hers' or 'his'")

    user = db.query(User).filter(User.role == role).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User with role '{role}' not found")

    user.password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    db.commit()


def delete_data(db: Session, data_type: str) -> DeleteDataResponse:
    deleted = 0

    if data_type in ("chat", "all"):
        deleted += db.query(Message).delete()

    if data_type in ("timeline", "all"):
        deleted += db.query(TimelineEvent).delete()

    db.commit()
    return DeleteDataResponse(ok=True, deleted=deleted)
