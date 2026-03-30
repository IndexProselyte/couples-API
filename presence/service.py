from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from database import Presence, User
from presence.schemas import PresenceInfo, PresenceResponse


def get_presence(db: Session, user: User) -> PresenceResponse:
    partner = db.query(User).filter(
        User.id != user.id, User.role != "admin"
    ).first()

    your = _get_or_create(db, user.id)
    partner_row = _get_or_create(db, partner.id) if partner else None

    return PresenceResponse(
        your=_to_info(user.id, your),
        partner=_to_info(partner.id if partner else "", partner_row),
    )


def set_presence(db: Session, user_id: str, online: bool) -> PresenceInfo:
    row = _get_or_create(db, user_id)
    row.is_online = online
    row.last_seen = datetime.now(timezone.utc)
    db.commit()
    return _to_info(user_id, row)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _get_or_create(db: Session, user_id: str) -> Presence:
    row = db.query(Presence).filter(Presence.user_id == user_id).first()
    if not row:
        row = Presence(user_id=user_id, is_online=False)
        db.add(row)
        db.commit()
    return row


def _to_info(user_id: str, row: Presence | None) -> PresenceInfo:
    if not row:
        return PresenceInfo(user_id=user_id, is_online=False, last_seen=None)
    return PresenceInfo(
        user_id=user_id,
        is_online=bool(row.is_online),
        last_seen=row.last_seen.isoformat() + "Z" if row.last_seen else None,
    )
