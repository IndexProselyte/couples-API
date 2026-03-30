from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from database import Message, Presence, User
from stats.schemas import StatsResponse


def get_stats(db: Session, user: User) -> StatsResponse:
    # ── Message counts ────────────────────────────────────────────────────────
    sent_msgs = (
        db.query(Message)
        .filter(Message.sender_id == user.id, Message.deleted.is_(False))
        .all()
    )
    received_msgs = (
        db.query(Message)
        .filter(Message.sender_id != user.id, Message.deleted.is_(False))
        .all()
    )

    messages_sent     = len(sent_msgs)
    messages_received = len(received_msgs)

    # ── Data volume — text bytes + file sizes ─────────────────────────────────
    def _msg_bytes(msgs: list) -> int:
        total = 0
        for m in msgs:
            total += len((m.text or "").encode("utf-8"))
            if m.file_size:
                total += m.file_size
        return total

    data_tx_bytes = _msg_bytes(sent_msgs)
    data_rx_bytes = _msg_bytes(received_msgs)

    # ── Presence / session data ───────────────────────────────────────────────
    presence = db.query(Presence).filter(Presence.user_id == user.id).first()

    connection_drops = int(presence.connection_drops or 0) if presence else 0

    last_connected: str | None = None
    if presence and presence.connected_at:
        last_connected = presence.connected_at.isoformat() + "Z"

    # uptime = seconds since connected_at if currently online, else 0
    uptime_seconds = 0
    if presence and presence.is_online and presence.connected_at:
        connected_at = presence.connected_at
        if connected_at.tzinfo is None:
            connected_at = connected_at.replace(tzinfo=timezone.utc)
        uptime_seconds = max(
            0, int((datetime.now(timezone.utc) - connected_at).total_seconds())
        )

    return StatsResponse(
        messages_sent=messages_sent,
        messages_received=messages_received,
        data_tx_bytes=data_tx_bytes,
        data_rx_bytes=data_rx_bytes,
        uptime_seconds=uptime_seconds,
        connection_drops=connection_drops,
        last_connected=last_connected,
    )
