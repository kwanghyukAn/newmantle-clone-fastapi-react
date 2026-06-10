from __future__ import annotations

import json
from collections import defaultdict

from fastapi import WebSocket

from app.models.schemas import RoomState


class RoomBroadcaster:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, room_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[room_id].add(websocket)

    def disconnect(self, room_id: str, websocket: WebSocket) -> None:
        room_connections = self._connections.get(room_id)
        if room_connections is None:
            return
        room_connections.discard(websocket)
        if not room_connections:
            self._connections.pop(room_id, None)

    async def broadcast_state(self, room_id: str, state: RoomState) -> None:
        payload = json.dumps(state.model_dump(mode="json"), ensure_ascii=False)
        stale: list[WebSocket] = []
        for websocket in self._connections.get(room_id, set()):
            try:
                await websocket.send_text(payload)
            except Exception:
                stale.append(websocket)
        for websocket in stale:
            self.disconnect(room_id, websocket)
