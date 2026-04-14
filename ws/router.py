from __future__ import annotations

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder # <-- 1. Import this
from jose import JWTError

from auth.service import decode_token
from database import Presence, SessionLocal
from presence.service import set_presence
from ws.manager import manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, token: str = Query(...)):
    """Authenticate via ?token=<jwt> then relay real-time events."""
    try:
        payload = decode_token(token)
        user_id: str | None = payload.get("sub")
        if not user_id:
            await ws.close(code=4001)
            return
    except JWTError:
        await ws.close(code=4001)
        return

    await manager.connect(user_id, ws)

    # Mark online, record connected_at, notify partner.
    db = SessionLocal()
    try:
        from datetime import datetime, timezone
        presence = set_presence(db, user_id, online=True)
        row = db.query(Presence).filter(Presence.user_id == user_id).first()
        if row:
            row.connected_at = datetime.now(timezone.utc)
            db.commit()
            
        await manager.broadcast(
            {"type": "partner_presence", "data": {
                "user_id": presence.user_id,
                "is_online": presence.is_online,
                # 2. Safely encode the datetime to an ISO string
                "last_seen": jsonable_encoder(presence.last_seen), 
            }},
            exclude_user_id=user_id,
        )
    finally:
        db.close()

    try:
        while True:
            data = await ws.receive_json()
            frame_type = data.get("type")

            if frame_type == "typing":
                await manager.broadcast(
                    {"type": "partner_typing", "data": data.get("data", {})},
                    exclude_user_id=user_id,
                )

            elif frame_type == "presence":
                online: bool = bool(data.get("data", {}).get("online", False))
                db = SessionLocal()
                try:
                    presence = set_presence(db, user_id, online)
                    await manager.broadcast(
                        {
                            "type": "partner_presence",
                            "data": {
                                "user_id": presence.user_id,
                                "is_online": presence.is_online,
                                "last_seen": jsonable_encoder(presence.last_seen),
                            },
                        },
                        exclude_user_id=user_id,
                    )
                finally:
                    db.close()

    except (WebSocketDisconnect, Exception):
        pass
    finally:
        manager.disconnect(user_id)
        # Mark offline, increment connection_drops, notify partner.
        db = SessionLocal()
        try:
            row = db.query(Presence).filter(Presence.user_id == user_id).first()
            if row:
                row.connection_drops = (row.connection_drops or 0) + 1
                db.commit()
            presence = set_presence(db, user_id, online=False)
            
            await manager.broadcast(
                {"type": "partner_presence", "data": {
                    "user_id": presence.user_id,
                    "is_online": presence.is_online,
                    # 3. Safely encode the datetime here too
                    "last_seen": jsonable_encoder(presence.last_seen),
                }},
                exclude_user_id=user_id,
            )
        finally:
            db.close()