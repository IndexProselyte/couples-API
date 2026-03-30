from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class StatsResponse(BaseModel):
    messages_sent:     int
    messages_received: int
    data_tx_bytes:     int
    data_rx_bytes:     int
    uptime_seconds:    int
    connection_drops:  int
    last_connected:    Optional[str] = None  # ISO 8601 UTC
