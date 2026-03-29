from __future__ import annotations

from fastapi import WebSocket


class ConnectionManager:
    """Tracks the (at most 2) active WebSocket connections by user_id."""

    def __init__(self) -> None:
        self._connections: dict[str, WebSocket] = {}

    async def connect(self, user_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._connections[user_id] = ws

    def disconnect(self, user_id: str) -> None:
        self._connections.pop(user_id, None)

    async def broadcast(
        self, message: dict, exclude_user_id: str | None = None
    ) -> None:
        """Send *message* to every connected socket except the excluded one."""
        for uid, ws in list(self._connections.items()):
            if uid == exclude_user_id:
                continue
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(uid)

    async def send_to(self, user_id: str, message: dict) -> None:
        ws = self._connections.get(user_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(user_id)


# Singleton shared across the entire process.
manager = ConnectionManager()
