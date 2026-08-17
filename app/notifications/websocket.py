"""
WebSocket connection manager.

Keeps a per-user_id list of active WebSocket connections so the
scheduler (or any API endpoint) can push a JSON notification straight
to that user's open browser tab(s) in real time, without polling.
"""
import json
from typing import Dict, List
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(user_id, []).append(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket):
        conns = self.active_connections.get(user_id, [])
        if websocket in conns:
            conns.remove(websocket)
        if not conns and user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_to_user(self, user_id: int, data: dict):
        conns = self.active_connections.get(user_id, [])
        stale = []
        for ws in conns:
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                stale.append(ws)
        for ws in stale:
            self.disconnect(user_id, ws)

    async def broadcast(self, data: dict):
        for user_id in list(self.active_connections.keys()):
            await self.send_to_user(user_id, data)


# Single shared instance used across the app (imported by main.py and the scheduler).
manager = ConnectionManager()
