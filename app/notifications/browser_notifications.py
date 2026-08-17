"""
Browser notification support.

Actual browser push requires the frontend's Notification API (see
frontend/js/notifications.js) — the backend's role is just to shape a
consistent payload the frontend can hand straight to
`new Notification(title, options)`. This function is used both by the
WebSocket messages and by the /notifications/pending REST endpoint
(used as a fallback for browsers/tabs that missed the WS push).
"""
from typing import Optional


def build_browser_payload(title: str, body: str, icon: Optional[str] = None, tag: Optional[str] = None) -> dict:
    return {
        "title": title,
        "options": {
            "body": body,
            "icon": icon or "/static/icon.png",
            "tag": tag,
            "requireInteraction": False,
        },
    }
