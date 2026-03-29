from __future__ import annotations

import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from database import Message, User
from messages.schemas import MessageCreate, MessageResponse


def get_messages(
    db: Session, user: User, limit: int, before: str | None
) -> dict:
    query = db.query(Message).filter(Message.deleted.is_(False))

    if before:
        cursor = db.query(Message).filter(Message.id == before).first()
        if cursor:
            query = query.filter(Message.created_at < cursor.created_at)

    # Fetch the window newest-first so LIMIT picks the right boundary,
    # then reverse so the client receives oldest → newest.
    rows = query.order_by(Message.created_at.desc()).limit(limit).all()
    rows = list(reversed(rows))

    result: list[MessageResponse] = []
    seen_dates: set[str] = set()

    for msg in rows:
        day = msg.created_at.strftime("%Y-%m-%d")
        date_label = day if day not in seen_dates else None
        seen_dates.add(day)
        result.append(_to_response(msg, user.id, date_label))

    return {"messages": [r.model_dump() for r in result]}


def create_message(
    db: Session, user: User, body: MessageCreate
) -> MessageResponse:
    # Resolve the sender of the quoted message so we can serve the correct
    # reply_to_is_sent for both users without trusting the client boolean.
    reply_to_sender_id: str | None = None
    if body.reply_to_id:
        original = (
            db.query(Message)
            .filter(
                Message.id == body.reply_to_id,
                Message.deleted.is_(False),
            )
            .first()
        )
        if original:
            reply_to_sender_id = original.sender_id

    msg = Message(
        id=str(uuid.uuid4()),
        sender_id=user.id,
        text=body.text,
        reply_to_id=body.reply_to_id,
        reply_to_text=body.reply_to_text,
        reply_to_sender_id=reply_to_sender_id,
        reactions=[],
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    # Set date only if this is the first message of the calendar day.
    day = msg.created_at.strftime("%Y-%m-%d")
    day_start = msg.created_at.replace(hour=0, minute=0, second=0, microsecond=0)
    earlier_today = (
        db.query(Message)
        .filter(
            Message.created_at >= day_start,
            Message.created_at < msg.created_at,
            Message.deleted.is_(False),
        )
        .count()
    )
    date_label = day if earlier_today == 0 else None

    return _to_response(msg, user.id, date_label)


def update_reactions(
    db: Session, msg_id: str, emoji: str, action: str
) -> dict:
    msg = (
        db.query(Message)
        .filter(Message.id == msg_id, Message.deleted.is_(False))
        .first()
    )
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    reactions: list[str] = list(msg.reactions or [])
    if action == "add":
        if emoji not in reactions:
            reactions.append(emoji)
    else:  # "remove"
        reactions = [r for r in reactions if r != emoji]

    msg.reactions = reactions
    flag_modified(msg, "reactions")
    db.commit()
    return {"reactions": reactions}


def star_message(db: Session, msg_id: str, starred: bool) -> None:
    msg = db.query(Message).filter(Message.id == msg_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    msg.is_starred = starred
    db.commit()


def delete_message(db: Session, msg_id: str) -> None:
    msg = db.query(Message).filter(Message.id == msg_id).first()
    if msg:
        msg.deleted = True
        db.commit()


# ── Internal ──────────────────────────────────────────────────────────────────


def _to_response(
    msg: Message, user_id: str, date_label: str | None
) -> MessageResponse:
    reply_to_is_sent: bool | None = None
    if msg.reply_to_sender_id is not None:
        reply_to_is_sent = msg.reply_to_sender_id == user_id

    return MessageResponse(
        id=msg.id,
        text=msg.text or "",
        is_sent=msg.sender_id == user_id,
        time=msg.created_at.strftime("%H:%M"),
        date=date_label,
        is_file=bool(msg.is_file),
        file_name=msg.file_name,
        file_size=msg.file_size,
        image_url=msg.image_url,
        sticker_path=msg.sticker_path,
        reactions=list(msg.reactions or []),
        is_starred=bool(msg.is_starred),
        is_voice=bool(msg.is_voice),
        voice_duration_ms=msg.voice_duration_ms,
        voice_waveform=msg.voice_waveform,
        reply_to_text=msg.reply_to_text,
        reply_to_is_sent=reply_to_is_sent,
    )
