/* ==========================================================================
   notifications.js — WebSocket live connection + browser notifications.
   ========================================================================== */

let notifSocket = null;
let unreadCount = 0;

function connectNotifications() {
  const token = Auth.getToken();
  if (!token) return;

  const protocol = location.protocol === "https:" ? "wss" : "ws";
  notifSocket = new WebSocket(`${protocol}://${location.host}/ws/notifications?token=${encodeURIComponent(token)}`);

  notifSocket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleIncomingNotification(data);
    } catch (e) { /* ignore malformed payloads */ }
  };

  notifSocket.onclose = () => {
    // Reconnect after a short delay (handles server restarts / brief drops).
    setTimeout(() => { if (Auth.isLoggedIn()) connectNotifications(); }, 4000);
  };
}

function handleIncomingNotification(data) {
  const message = data.message || "You have a new notification";
  toast(message);
  bumpNotifDot();
  maybeShowBrowserNotification("StudySync", message);
}

function bumpNotifDot() {
  unreadCount += 1;
  const dot = document.getElementById("notif-dot");
  if (dot) dot.style.display = "block";
}

function clearNotifDot() {
  unreadCount = 0;
  const dot = document.getElementById("notif-dot");
  if (dot) dot.style.display = "none";
}

async function requestBrowserNotificationPermission() {
  if (!("Notification" in window)) return;
  if (Notification.permission === "default") {
    await Notification.requestPermission();
  }
}

function maybeShowBrowserNotification(title, body) {
  if (!("Notification" in window)) return;
  if (Notification.permission === "granted" && document.visibilityState !== "visible") {
    new Notification(title, { body, icon: "/static/icon.png" });
  }
}

async function loadPendingReminders() {
  try {
    const pending = await api("/api/reminders/pending");
    if (pending.length) bumpNotifDot();
    return pending;
  } catch (e) {
    return [];
  }
}
