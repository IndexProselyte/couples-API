from __future__ import annotations

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from jose import JWTError

from auth.service import decode_token
from ws.manager import manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, token: str = Query(...)):
    """Authenticate via ?token=<jwt> then relay real-time events.

    Server → Client frame types:
      { "type": "message",        "data": <ChatMessage> }
      { "type": "message_update", "data": { "id": ..., "reactions": [...] | "is_starred": bool } }
      { "type": "message_delete", "data": { "id": ... } }
      { "type": "partner_typing", "data": { "typing": bool } }

    Client → Server frame types:
      { "type": "typing", "data": { "typing": bool } }
    """
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
    try:
        while True:
            data = await ws.receive_json()
            if data.get("type") == "typing":
                await manager.broadcast(
                    {"type": "partner_typing", "data": data.get("data", {})},
                    exclude_user_id=user_id,
                )
    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception:
        manager.disconnect(user_id)
