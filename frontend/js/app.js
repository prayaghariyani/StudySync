/* ==========================================================================
   app.js — shared core: API client, auth/session, theme, toasts,
   command palette, keyboard shortcuts. Loaded on every page.
   ========================================================================== */

const API_BASE = ""; // same-origin; app is served by FastAPI itself

const Auth = {
  getToken() { return localStorage.getItem("studysync_token"); },
  setToken(t) { localStorage.setItem("studysync_token", t); },
  clear() { localStorage.removeItem("studysync_token"); localStorage.removeItem("studysync_user"); },
  getUser() { const u = localStorage.getItem("studysync_user"); return u ? JSON.parse(u) : null; },
  setUser(u) { localStorage.setItem("studysync_user", JSON.stringify(u)); },
  isLoggedIn() { return !!this.getToken(); },
};

const Loading = {
  pending: 0,
  overlay: null,
  showTimer: null,
  delayMs: 120,
};

function ensureLoadingOverlay() {
  if (Loading.overlay) return Loading.overlay;
  const overlay = document.createElement("div");
  overlay.className = "global-loading";
  overlay.setAttribute("aria-hidden", "true");
  overlay.innerHTML = `
    <div class="global-loading-panel" role="status" aria-live="polite">
      <div class="global-loading-spinner"></div>
      <div class="global-loading-text">Loading...</div>
    </div>
  `;
  document.body.appendChild(overlay);
  Loading.overlay = overlay;
  return overlay;
}

function showLoading(message = "Loading...") {
  Loading.pending += 1;
  const overlay = ensureLoadingOverlay();
  const text = overlay.querySelector(".global-loading-text");
  if (text) text.textContent = message;

  if (Loading.pending === 1) {
    Loading.showTimer = window.setTimeout(() => {
      overlay.classList.add("visible");
      overlay.setAttribute("aria-hidden", "false");
      document.body.classList.add("is-busy");
    }, Loading.delayMs);
  }
}

function hideLoading() {
  Loading.pending = Math.max(0, Loading.pending - 1);
  if (Loading.pending > 0) return;

  window.clearTimeout(Loading.showTimer);
  Loading.showTimer = null;
  if (!Loading.overlay) return;
  Loading.overlay.classList.remove("visible");
  Loading.overlay.setAttribute("aria-hidden", "true");
  document.body.classList.remove("is-busy");
}

async function withLoading(task, message = "Loading...") {
  showLoading(message);
  try {
    return await task();
  } finally {
    hideLoading();
  }
}

async function appFetch(url, options, message = "Loading...") {
  return withLoading(() => fetch(url, options), message);
}

async function api(path, { method = "GET", body, headers = {} } = {}) {
  const opts = { method, headers: { ...headers } };
  if (body !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const token = Auth.getToken();
  if (token) opts.headers["Authorization"] = `Bearer ${token}`;

  const action = method === "GET" ? "Loading..." : "Processing...";
  const res = await appFetch(API_BASE + path, opts, action);
  if (res.status === 401) {
    Auth.clear();
    if (!location.pathname.endsWith("index.html") && location.pathname !== "/") {
      location.href = "/";
    }
    throw new Error("Unauthorized");
  }
  if (res.status === 204) return null;

  const isJson = (res.headers.get("content-type") || "").includes("application/json");
  const data = isJson ? await res.json() : await res.text();
  if (!res.ok) {
    const message = (data && data.detail) ? data.detail : "Something went wrong";
    throw new Error(message);
  }
  return data;
}

/* ---------------- Toasts ---------------- */
function toast(message, type = "default") {
  let container = document.querySelector(".toast-container");
  if (!container) {
    container = document.createElement("div");
    container.className = "toast-container";
    document.body.appendChild(container);
  }
  const el = document.createElement("div");
  el.className = `toast ${type === "error" ? "toast-danger" : ""}`;
  el.textContent = message;
  container.appendChild(el);
  setTimeout(() => el.remove(), 4500);
}

/* ---------------- Theme ---------------- */
function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme === "dark" ? "dark" : "light");
}

function initTheme() {
  const user = Auth.getUser();
  const saved = localStorage.getItem("studysync_theme") || (user && user.theme) || "light";
  applyTheme(saved);
}

async function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
  const next = current === "dark" ? "light" : "dark";
  applyTheme(next);
  localStorage.setItem("studysync_theme", next);
  if (Auth.isLoggedIn()) {
    try { await api("/api/auth/me", { method: "PATCH", body: { theme: next } }); } catch (e) { /* non-fatal */ }
  }
}

/* ---------------- Command palette (Ctrl/Cmd+K) ---------------- */
function buildCommandPalette(actions) {
  document.addEventListener("keydown", (e) => {
    const mod = e.metaKey || e.ctrlKey;
    if (mod && e.key.toLowerCase() === "k") {
      e.preventDefault();
      openCommandPalette(actions);
    }
    if (e.key === "Escape") closeCommandPalette();
  });
}

function openCommandPalette(actions) {
  closeCommandPalette();
  const backdrop = document.createElement("div");
  backdrop.className = "cmdk-backdrop";
  backdrop.id = "cmdk-backdrop";
  backdrop.innerHTML = `
    <div class="cmdk">
      <input type="text" placeholder="Type a command or search..." id="cmdk-input" autofocus />
      <div class="cmdk-results" id="cmdk-results"></div>
    </div>`;
  backdrop.addEventListener("click", (e) => { if (e.target.id === "cmdk-backdrop") closeCommandPalette(); });
  document.body.appendChild(backdrop);

  const input = document.getElementById("cmdk-input");
  const results = document.getElementById("cmdk-results");

  function render(filter = "") {
    const f = filter.toLowerCase();
    const matches = actions.filter(a => a.label.toLowerCase().includes(f));
    results.innerHTML = matches.map((a, i) =>
      `<div class="cmdk-item" data-index="${i}"><span>${a.label}</span><span class="mono" style="color:var(--fg-dim)">${a.hint || ""}</span></div>`
    ).join("") || `<div class="cmdk-item">No matches</div>`;
    [...results.children].forEach((el, i) => {
      el.addEventListener("click", () => { matches[i].action(); closeCommandPalette(); });
    });
  }
  render();
  input.addEventListener("input", () => render(input.value));
  input.focus();
}

function closeCommandPalette() {
  const el = document.getElementById("cmdk-backdrop");
  if (el) el.remove();
}

/* ---------------- Lucide icon refresh helper ---------------- */
function refreshIcons() {
  if (window.lucide) window.lucide.createIcons();
}

/* ---------------- Formatting helpers ---------------- */
function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}
function formatDateTime(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
}
function timeUntil(iso) {
  const diffMs = new Date(iso) - new Date();
  const hours = diffMs / 36e5;
  if (hours < 0) return "Overdue";
  if (hours < 1) return `${Math.round(hours * 60)}m left`;
  if (hours < 24) return `${Math.round(hours)}h left`;
  return `${Math.round(hours / 24)}d left`;
}
function priorityChipClass(priority) {
  return `chip chip-${(priority || "medium").toLowerCase()}`;
}

/* Guard: redirect unauthenticated users away from app pages */
function requireAuth() {
  if (!Auth.isLoggedIn()) location.href = "/";
}

initTheme();
