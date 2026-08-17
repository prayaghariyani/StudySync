"""
WebSocket endpoint for real-time notifications.

Browsers can't set Authorization headers on a WebSocket handshake, so
the JWT is passed as a query parameter (?token=...) instead — a
standard pattern for WS auth. The token is validated the same way as
the REST endpoints via decode_access_token.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.models.user import User
from app.utils.security import decode_access_token
from app.notifications.websocket import manager

router = APIRouter()


@router.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket, token: str = Query(...)):
    payload = decode_access_token(token)
    if not payload or "user_id" not in payload:
        await websocket.close(code=4401)
        return

    db: Session = SessionLocal()
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    db.close()
    if not user:
        await websocket.close(code=4401)
        return

    await manager.connect(user.id, websocket)
    try:
        while True:
            # We don't expect the client to send anything meaningful, but
            # we must keep receiving to detect disconnects promptly.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user.id, websocket)
