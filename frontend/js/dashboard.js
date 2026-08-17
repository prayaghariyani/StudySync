/* ==========================================================================
   dashboard.js — application shell: sidebar/navbar loading, view router,
   and every view that isn't broken out into its own file (dashboard home,
   subjects, exams, study sessions/pomodoro, analytics, settings).
   ========================================================================== */

requireAuth();

const VIEWS = ["dashboard", "tasks", "exams", "calendar", "sessions", "subjects", "analytics", "settings"];
let activeView = "dashboard";
let pomodoroTimer = null;

async function bootApp() {
  await loadPartial("sidebar", "#sidebar");
  await loadPartial("navbar", "#navbar");
  wireShell();
  await refreshSidebarStats();
  await loadSubjectsIntoCache();

  connectNotifications();
  requestBrowserNotificationPermission();
  loadPendingReminders();

  const initialView = (location.hash || "#dashboard").replace("#", "");
  switchView(VIEWS.includes(initialView) ? initialView : "dashboard");
}

async function loadPartial(name, selector) {
  const res = await appFetch(`/components/${name}.html`, undefined, "Loading interface...");
  const html = await res.text();
  document.querySelector(selector).innerHTML = html;
}

function wireShell() {
  document.querySelectorAll(".nav-item[data-view]").forEach(item => {
    item.addEventListener("click", (e) => {
      e.preventDefault();
      switchView(item.dataset.view);
      closeSidebar();
    });
  });

  document.getElementById("logout-btn").addEventListener("click", () => {
    Auth.clear();
    location.href = "/";
  });

  document.getElementById("theme-toggle-btn").addEventListener("click", async () => {
    await toggleTheme();
    updateThemeIcon();
  });
  updateThemeIcon();

  document.getElementById("open-cmdk").addEventListener("click", () => openCommandPalette(buildActions()));

  document.getElementById("notif-btn").addEventListener("click", () => {
    clearNotifDot();
    switchView("dashboard");
  });

  const user = Auth.getUser();
  if (user) document.getElementById("navbar-username").textContent = user.name;

  wireHamburgerMenu();
  buildCommandPalette(buildActions());
}

/* ---------------- Hamburger / off-canvas sidebar (mobile) ---------------- */
function wireHamburgerMenu() {
  const hamburgerBtn = document.getElementById("hamburger-btn");
  const sidebar = document.getElementById("sidebar");
  const backdrop = document.getElementById("sidebar-backdrop");
  if (!hamburgerBtn || !sidebar || !backdrop) return;

  hamburgerBtn.addEventListener("click", () => {
    const isOpen = sidebar.classList.contains("open");
    isOpen ? closeSidebar() : openSidebar();
  });
  backdrop.addEventListener("click", closeSidebar);

  // Escape closes the menu; resizing past the mobile breakpoint resets it
  // so the sidebar doesn't stay "open" (and the backdrop stuck) once it's
  // back to being permanently visible on desktop.
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeSidebar(); });
  window.addEventListener("resize", () => { if (window.innerWidth > 900) closeSidebar(); });
}

function openSidebar() {
  document.getElementById("sidebar").classList.add("open");
  document.getElementById("sidebar-backdrop").classList.add("visible");
  const btn = document.getElementById("hamburger-btn");
  btn.classList.add("is-open");
  btn.setAttribute("aria-expanded", "true");
  document.body.style.overflow = "hidden";
}

function closeSidebar() {
  const sidebar = document.getElementById("sidebar");
  const backdrop = document.getElementById("sidebar-backdrop");
  const btn = document.getElementById("hamburger-btn");
  if (sidebar) sidebar.classList.remove("open");
  if (backdrop) backdrop.classList.remove("visible");
  if (btn) { btn.classList.remove("is-open"); btn.setAttribute("aria-expanded", "false"); }
  document.body.style.overflow = "";
}

function buildActions() {
  return [
    { label: "Go to Dashboard", hint: "nav", action: () => switchView("dashboard") },
    { label: "Go to Tasks", hint: "nav", action: () => switchView("tasks") },
    { label: "Go to Exams", hint: "nav", action: () => switchView("exams") },
    { label: "Go to Calendar", hint: "nav", action: () => switchView("calendar") },
    { label: "Go to Study Sessions", hint: "nav", action: () => switchView("sessions") },
    { label: "Go to Subjects", hint: "nav", action: () => switchView("subjects") },
    { label: "Go to Analytics", hint: "nav", action: () => switchView("analytics") },
    { label: "New task", hint: "action", action: () => { switchView("tasks"); setTimeout(() => openTaskModal(), 150); } },
    { label: "Toggle dark mode", hint: "action", action: async () => { await toggleTheme(); updateThemeIcon(); } },
    { label: "Export CSV", hint: "action", action: () => { window.location.href = "/api/export/csv"; } },
    { label: "Export calendar (.ics)", hint: "action", action: () => { window.location.href = "/api/export/ics"; } },
  ];
}

function updateThemeIcon() {
  const isDark = document.documentElement.getAttribute("data-theme") === "dark";
  const icon = document.getElementById("theme-icon");
  if (icon) { icon.setAttribute("data-lucide", isDark ? "sun" : "moon"); refreshIcons(); }
}

function switchView(view) {
  activeView = view;
  location.hash = view;
  document.querySelectorAll(".nav-item[data-view]").forEach(item => {
    item.classList.toggle("active", item.dataset.view === view);
  });
  const container = document.querySelector("#main-content");
  container.innerHTML = `<div class="skeleton" style="height:120px"></div>`;

  const renderers = {
    dashboard: renderDashboardHome,
    tasks: renderTasksView,
    exams: renderExamsView,
    calendar: renderCalendarView,
    sessions: renderSessionsView,
    subjects: renderSubjectsView,
    analytics: renderAnalyticsView,
    settings: renderSettingsView,
  };
  renderers[view](container);
}

async function refreshSidebarStats() {
  try {
    const overview = await api("/api/analytics/overview");
    const streakEl = document.getElementById("sidebar-streak");
    const levelEl = document.getElementById("sidebar-level");
    if (streakEl) streakEl.textContent = `${overview.streak_days} day streak`;
    if (levelEl) levelEl.textContent = `Level ${overview.level} · ${overview.xp} XP`;
  } catch (e) { /* non-fatal on first load before any semester exists */ }
}

/* ---------------- Dashboard home ---------------- */
async function renderDashboardHome(container) {
  const user = Auth.getUser();
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";

  container.innerHTML = `
    <div class="lamp-glow" style="margin-bottom:22px">
      <h1 style="font-size:26px">${greeting}, ${user ? escapeHtml(user.name.split(" ")[0]) : ""} 👋</h1>
      <p style="color:var(--fg-dim);margin-top:4px">Here's what needs your focus today.</p>
    </div>
    <div class="stat-grid" id="dash-stats" style="margin-bottom:24px"></div>
    <div style="display:grid;grid-template-columns:1.3fr 1fr;gap:20px" id="dash-columns"></div>
  `;

  try {
    const summary = await api("/api/dashboard/summary");

    document.getElementById("dash-stats").innerHTML = `
      <div class="card stat-card"><div class="num">${summary.greeting_counts.subjects}</div><div class="label">📚 Subjects</div></div>
      <div class="card stat-card"><div class="num">${summary.greeting_counts.tasks}</div><div class="label">📝 Open tasks</div></div>
      <div class="card stat-card"><div class="num">${summary.greeting_counts.exams}</div><div class="label">🧪 Upcoming exams</div></div>
    `;

    const todayHtml = summary.today.length
      ? summary.today.map(t => `<div class="card task-card"><div style="flex:1"><div class="title">${escapeHtml(t.title)}</div><div class="meta"><span class="mono">${formatDateTime(t.due_date)}</span><span class="${priorityChipClass(t.priority)}">${t.priority}</span></div></div></div>`).join("")
      : `<div class="empty-state card">Nothing due today. Enjoy the breathing room.</div>`;

    const upcomingHtml = (summary.due_soon.slice(0, 5).map(t => `<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border);font-size:13px"><span>${escapeHtml(t.title)}</span><span class="mono" style="color:var(--fg-dim)">${formatDate(t.due_date)}</span></div>`).join("")) || `<div style="color:var(--fg-dim);font-size:13px">Nothing due soon.</div>`;

    document.getElementById("dash-columns").innerHTML = `
      <div>
        <h3 style="margin-bottom:12px;font-size:16px">🔥 Today</h3>
        ${todayHtml}
      </div>
      <div>
        <div class="card" style="padding:16px;margin-bottom:16px">
          <h3 style="font-size:15px;margin-bottom:10px">Upcoming</h3>
          ${upcomingHtml}
        </div>
        <div class="card" style="padding:16px">
          <h3 style="font-size:15px;margin-bottom:10px">Semester progress</h3>
          <div class="progress-bar"><div class="progress-bar-fill" style="width:${summary.progress.percent_complete}%"></div></div>
          <div class="mono" style="font-size:12px;color:var(--fg-dim);margin-top:6px">${summary.progress.completed}/${summary.progress.total} tasks · ${summary.progress.percent_complete}%</div>
        </div>
      </div>
    `;
  } catch (e) {
    container.querySelector("#dash-columns").innerHTML = `<div class="empty-state card">Add a semester and subject to get started. <br><button class="btn btn-primary" style="margin-top:12px" onclick="switchView('subjects')">Go to Subjects</button></div>`;
  }
  refreshIcons();
}

/* ---------------- Exams ---------------- */
async function renderExamsView(container) {
  container.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <h2>Exams</h2>
      <button class="btn btn-primary" id="new-exam-btn"><i data-lucide="plus" width="16"></i> New exam</button>
    </div>
    <div id="exam-list"></div>`;
  refreshIcons();
  await loadSubjectsIntoCache();
  document.getElementById("new-exam-btn").addEventListener("click", () => openExamModal());
  await loadExamList();
}

async function loadExamList() {
  const listEl = document.getElementById("exam-list");
  const exams = await api("/api/exams");
  if (!exams.length) {
    listEl.innerHTML = `<div class="empty-state card">No exams scheduled yet.</div>`;
    return;
  }
  listEl.innerHTML = exams.map(e => `
    <div class="card task-card" style="border-left-color:var(--danger)">
      <div style="flex:1">
        <div class="title">${escapeHtml(e.title)} <span style="color:var(--fg-dim);font-weight:400">— ${subjectName(e.subject_id)}</span></div>
        <div class="meta"><span class="mono">${formatDateTime(e.exam_date)}</span><span>${e.location || "No location set"}</span><span>${timeUntil(e.exam_date)}</span></div>
      </div>
      <button class="icon-btn" data-id="${e.id}" data-action="del-exam"><i data-lucide="trash-2" width="15"></i></button>
    </div>`).join("");
  refreshIcons();
  listEl.querySelectorAll('[data-action="del-exam"]').forEach(btn => {
    btn.addEventListener("click", async () => {
      if (!confirm("Delete this exam?")) return;
      await api(`/api/exams/${btn.dataset.id}`, { method: "DELETE" });
      loadExamList();
    });
  });
}

function openExamModal() {
  const backdrop = document.createElement("div");
  backdrop.className = "modal-backdrop";
  backdrop.innerHTML = `
    <div class="modal">
      <h3>New exam</h3>
      <form id="exam-form">
        <div class="form-row"><label>Title</label><input id="ef-title" required /></div>
        <div class="form-grid">
          <div class="form-row"><label>Subject</label><select id="ef-subject">${cachedSubjects.map(s => `<option value="${s.id}">${escapeHtml(s.name)}</option>`).join("")}</select></div>
          <div class="form-row"><label>Type</label><select id="ef-type">${["quiz", "mid_semester", "end_semester", "practical", "viva", "other"].map(t => `<option value="${t}">${t}</option>`).join("")}</select></div>
        </div>
        <div class="form-row"><label>Date &amp; time</label><input id="ef-date" type="datetime-local" required /></div>
        <div class="form-grid">
          <div class="form-row"><label>Duration (min)</label><input id="ef-duration" type="number" value="60" /></div>
          <div class="form-row"><label>Location</label><input id="ef-location" /></div>
        </div>
        <div class="form-row"><label>Notes</label><textarea id="ef-notes" rows="2"></textarea></div>
        <div style="display:flex;gap:10px;margin-top:16px">
          <button type="submit" class="btn btn-primary" style="flex:1;justify-content:center">Create exam</button>
          <button type="button" class="btn btn-ghost" id="ef-cancel">Cancel</button>
        </div>
      </form>
    </div>`;
  document.body.appendChild(backdrop);
  backdrop.addEventListener("click", (e) => { if (e.target === backdrop) backdrop.remove(); });
  document.getElementById("ef-cancel").addEventListener("click", () => backdrop.remove());
  document.getElementById("exam-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      await api("/api/exams", {
        method: "POST",
        body: {
          title: document.getElementById("ef-title").value,
          subject_id: Number(document.getElementById("ef-subject").value),
          exam_type: document.getElementById("ef-type").value,
          exam_date: new Date(document.getElementById("ef-date").value).toISOString(),
          duration: Number(document.getElementById("ef-duration").value) || 60,
          location: document.getElementById("ef-location").value,
          notes: document.getElementById("ef-notes").value,
        },
      });
      toast("Exam created");
      backdrop.remove();
      loadExamList();
    } catch (err) { toast(err.message, "error"); }
  });
}

/* ---------------- Study sessions + Pomodoro ---------------- */
async function renderSessionsView(container) {
  container.innerHTML = `
    <h2 style="margin-bottom:16px">Study Sessions</h2>
    <div style="display:grid;grid-template-columns:1fr 1.4fr;gap:20px">
      <div class="card" style="padding:22px;text-align:center">
        <h3 style="font-size:15px;margin-bottom:14px">Pomodoro Timer</h3>
        <div class="mono" id="pomo-display" style="font-size:44px;font-weight:700">25:00</div>
        <div style="display:flex;gap:8px;justify-content:center;margin-top:16px">
          <button class="btn btn-primary" id="pomo-start">Start</button>
          <button class="btn btn-ghost" id="pomo-reset">Reset</button>
        </div>
        <div class="mono" style="margin-top:14px;color:var(--fg-dim);font-size:12px" id="pomo-count">0 cycles completed today</div>
      </div>
      <div>
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
          <h3 style="font-size:15px">Logged sessions</h3>
          <button class="btn btn-primary" id="new-session-btn"><i data-lucide="plus" width="15"></i> Log session</button>
        </div>
        <div id="session-list"></div>
      </div>
    </div>`;
  refreshIcons();
  await loadSubjectsIntoCache();
  wirePomodoro();
  document.getElementById("new-session-btn").addEventListener("click", openSessionModal);
  await loadSessionList();
}

async function loadSessionList() {
  const listEl = document.getElementById("session-list");
  const sessions = await api("/api/study-sessions");
  if (!sessions.length) {
    listEl.innerHTML = `<div class="empty-state card">No sessions logged yet.</div>`;
    return;
  }
  listEl.innerHTML = sessions.slice(0, 12).map(s => `
    <div class="card task-card" style="border-left-color:var(--pine)">
      <div style="flex:1">
        <div class="title">${escapeHtml(s.title)} <span style="color:var(--fg-dim);font-weight:400">— ${subjectName(s.subject_id)}</span></div>
        <div class="meta"><span class="mono">${formatDateTime(s.start_time)}</span><span>${formatDurationMinutes(s.duration)}</span><span>${s.status}</span></div>
      </div>
    </div>`).join("");
}

function formatDurationMinutes(min) {
  const h = Math.floor(min / 60), m = min % 60;
  return h ? `${h}h ${m}m` : `${m}m`;
}

function openSessionModal() {
  const backdrop = document.createElement("div");
  backdrop.className = "modal-backdrop";
  backdrop.innerHTML = `
    <div class="modal">
      <h3>Log study session</h3>
      <form id="session-form">
        <div class="form-row"><label>Title</label><input id="sf-title" required placeholder="e.g. OS Memory Management" /></div>
        <div class="form-row"><label>Subject</label><select id="sf-subject">${cachedSubjects.map(s => `<option value="${s.id}">${escapeHtml(s.name)}</option>`).join("")}</select></div>
        <div class="form-grid">
          <div class="form-row"><label>Start</label><input id="sf-start" type="datetime-local" required /></div>
          <div class="form-row"><label>End</label><input id="sf-end" type="datetime-local" required /></div>
        </div>
        <div class="form-row"><label>Notes</label><textarea id="sf-notes" rows="2"></textarea></div>
        <div style="display:flex;gap:10px;margin-top:16px">
          <button type="submit" class="btn btn-primary" style="flex:1;justify-content:center">Log session</button>
          <button type="button" class="btn btn-ghost" id="sf-cancel">Cancel</button>
        </div>
      </form>
    </div>`;
  document.body.appendChild(backdrop);
  backdrop.addEventListener("click", (e) => { if (e.target === backdrop) backdrop.remove(); });
  document.getElementById("sf-cancel").addEventListener("click", () => backdrop.remove());
  document.getElementById("session-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      await api("/api/study-sessions", {
        method: "POST",
        body: {
          title: document.getElementById("sf-title").value,
          subject_id: Number(document.getElementById("sf-subject").value),
          start_time: new Date(document.getElementById("sf-start").value).toISOString(),
          end_time: new Date(document.getElementById("sf-end").value).toISOString(),
          notes: document.getElementById("sf-notes").value,
        },
      });
      toast("Session logged");
      backdrop.remove();
      loadSessionList();
    } catch (err) { toast(err.message, "error"); }
  });
}

function wirePomodoro() {
  let seconds = 25 * 60;
  let running = false;
  const display = document.getElementById("pomo-display");
  const startBtn = document.getElementById("pomo-start");

  function render() {
    const m = String(Math.floor(seconds / 60)).padStart(2, "0");
    const s = String(seconds % 60).padStart(2, "0");
    display.textContent = `${m}:${s}`;
  }

  document.getElementById("pomo-start").addEventListener("click", () => {
    running = !running;
    startBtn.textContent = running ? "Pause" : "Start";
    if (running) {
      pomodoroTimer = setInterval(() => {
        seconds -= 1;
        if (seconds <= 0) {
          clearInterval(pomodoroTimer);
          running = false;
          startBtn.textContent = "Start";
          toast("Pomodoro complete! Take a 5 minute break.");
          seconds = 25 * 60;
        }
        render();
      }, 1000);
    } else {
      clearInterval(pomodoroTimer);
    }
  });

  document.getElementById("pomo-reset").addEventListener("click", () => {
    clearInterval(pomodoroTimer);
    running = false;
    startBtn.textContent = "Start";
    seconds = 25 * 60;
    render();
  });
}

/* ---------------- Subjects ---------------- */
async function renderSubjectsView(container) {
  container.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <h2>Subjects</h2>
      <button class="btn btn-primary" id="new-subject-btn"><i data-lucide="plus" width="16"></i> New subject</button>
    </div>
    <div id="semester-banner" style="margin-bottom:14px"></div>
    <div class="stat-grid" id="subject-grid" style="grid-template-columns:repeat(3,1fr)"></div>`;
  refreshIcons();

  let semesters = await api("/api/semesters");
  const bannerEl = document.getElementById("semester-banner");
  if (!semesters.length) {
    bannerEl.innerHTML = `<div class="card" style="padding:16px"><b>Start by creating a semester.</b> <button class="btn btn-ghost" id="new-sem-btn" style="margin-left:10px">Create semester</button></div>`;
    document.getElementById("new-sem-btn").addEventListener("click", openSemesterModal);
  } else {
    bannerEl.innerHTML = `<div style="color:var(--fg-dim);font-size:13px">Active semester: <b style="color:var(--fg)">${escapeHtml(semesters[0].name)}</b></div>`;
  }

  document.getElementById("new-subject-btn").addEventListener("click", () => openSubjectModal(semesters));
  await loadSubjectGrid();
}

async function loadSubjectGrid() {
  await loadSubjectsIntoCache();
  const grid = document.getElementById("subject-grid");
  if (!cachedSubjects.length) {
    grid.innerHTML = `<div class="empty-state card" style="grid-column:1/-1">No subjects yet.</div>`;
    return;
  }
  grid.innerHTML = cachedSubjects.map(s => `
    <div class="card stat-card" style="border-left:4px solid ${s.color}">
      <div style="font-weight:700">${escapeHtml(s.name)}</div>
      <div style="color:var(--fg-dim);font-size:12px;margin-top:4px">${s.code || "—"} · ${s.teacher || "No teacher set"} · ${s.credits} credits</div>
    </div>`).join("");
}

function openSemesterModal() {
  const backdrop = document.createElement("div");
  backdrop.className = "modal-backdrop";
  backdrop.innerHTML = `
    <div class="modal">
      <h3>New semester</h3>
      <form id="sem-form">
        <div class="form-row"><label>Name</label><input id="sem-name" required placeholder="e.g. 2026 Semester 5" /></div>
        <div class="form-grid">
          <div class="form-row"><label>Start date</label><input id="sem-start" type="date" required /></div>
          <div class="form-row"><label>End date</label><input id="sem-end" type="date" required /></div>
        </div>
        <div style="display:flex;gap:10px;margin-top:16px">
          <button type="submit" class="btn btn-primary" style="flex:1;justify-content:center">Create</button>
          <button type="button" class="btn btn-ghost" id="sem-cancel">Cancel</button>
        </div>
      </form>
    </div>`;
  document.body.appendChild(backdrop);
  backdrop.addEventListener("click", (e) => { if (e.target === backdrop) backdrop.remove(); });
  document.getElementById("sem-cancel").addEventListener("click", () => backdrop.remove());
  document.getElementById("sem-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      await api("/api/semesters", {
        method: "POST",
        body: {
          name: document.getElementById("sem-name").value,
          start_date: document.getElementById("sem-start").value,
          end_date: document.getElementById("sem-end").value,
        },
      });
      toast("Semester created");
      backdrop.remove();
      switchView("subjects");
    } catch (err) { toast(err.message, "error"); }
  });
}

function openSubjectModal(semesters) {
  if (!semesters || !semesters.length) { toast("Create a semester first", "error"); return; }
  const backdrop = document.createElement("div");
  backdrop.className = "modal-backdrop";
  backdrop.innerHTML = `
    <div class="modal">
      <h3>New subject</h3>
      <form id="subj-form">
        <div class="form-row"><label>Name</label><input id="sf2-name" required placeholder="e.g. Operating Systems" /></div>
        <div class="form-grid">
          <div class="form-row"><label>Code</label><input id="sf2-code" placeholder="3160707" /></div>
          <div class="form-row"><label>Credits</label><input id="sf2-credits" type="number" value="4" /></div>
        </div>
        <div class="form-row"><label>Teacher</label><input id="sf2-teacher" /></div>
        <div class="form-row"><label>Color</label><input id="sf2-color" type="color" value="#e8a355" /></div>
        <div style="display:flex;gap:10px;margin-top:16px">
          <button type="submit" class="btn btn-primary" style="flex:1;justify-content:center">Create subject</button>
          <button type="button" class="btn btn-ghost" id="sf2-cancel">Cancel</button>
        </div>
      </form>
    </div>`;
  document.body.appendChild(backdrop);
  backdrop.addEventListener("click", (e) => { if (e.target === backdrop) backdrop.remove(); });
  document.getElementById("sf2-cancel").addEventListener("click", () => backdrop.remove());
  document.getElementById("subj-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      await api("/api/subjects", {
        method: "POST",
        body: {
          semester_id: semesters[0].id,
          name: document.getElementById("sf2-name").value,
          code: document.getElementById("sf2-code").value,
          credits: Number(document.getElementById("sf2-credits").value) || 0,
          teacher: document.getElementById("sf2-teacher").value,
          color: document.getElementById("sf2-color").value,
        },
      });
      toast("Subject created");
      backdrop.remove();
      loadSubjectGrid();
    } catch (err) { toast(err.message, "error"); }
  });
}

/* ---------------- Analytics ---------------- */
async function renderAnalyticsView(container) {
  container.innerHTML = `
    <h2 style="margin-bottom:16px">Analytics</h2>
    <div class="stat-grid" style="margin-bottom:20px" id="an-stats"></div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px">
      <div class="card" style="padding:18px"><h3 style="font-size:15px;margin-bottom:10px">Subject performance</h3><canvas id="chart-subjects" height="180"></canvas></div>
      <div class="card" style="padding:18px"><h3 style="font-size:15px;margin-bottom:10px">Task breakdown</h3><canvas id="chart-progress" height="180"></canvas></div>
    </div>
    <div class="card" style="padding:18px">
      <h3 style="font-size:15px;margin-bottom:10px">Study activity (last 90 days)</h3>
      <div class="heatmap-grid" id="heatmap"></div>
    </div>`;

  const overview = await api("/api/analytics/overview");
  document.getElementById("an-stats").innerHTML = `
    <div class="card stat-card"><div class="num">${overview.completion_rate}%</div><div class="label">Completion rate</div></div>
    <div class="card stat-card"><div class="num">${overview.on_time_rate}%</div><div class="label">On-time rate</div></div>
    <div class="card stat-card"><div class="num">${overview.study_efficiency}</div><div class="label">Tasks / study hour</div></div>
  `;

  const subjNames = Object.keys(overview.subject_performance);
  new Chart(document.getElementById("chart-subjects"), {
    type: "bar",
    data: { labels: subjNames, datasets: [{ label: "Completion %", data: Object.values(overview.subject_performance), backgroundColor: "#e8a355" }] },
    options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, max: 100 } } },
  });

  const p = overview.semester_progress;
  new Chart(document.getElementById("chart-progress"), {
    type: "doughnut",
    data: {
      labels: ["Completed", "In progress", "To do", "Overdue"],
      datasets: [{ data: [p.completed, p.in_progress, p.todo, p.overdue], backgroundColor: ["#2f5d55", "#e8a355", "#c9c2ae", "#c0533f"] }],
    },
  });

  const heatmap = await api("/api/analytics/heatmap?days=90");
  const heatmapEl = document.getElementById("heatmap");
  const minuteMap = Object.fromEntries(heatmap.map(h => [h.date, h.minutes]));
  const days = [];
  for (let i = 89; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    days.push(d.toISOString().slice(0, 10));
  }
  heatmapEl.innerHTML = days.map(d => {
    const minutes = minuteMap[d] || 0;
    const intensity = minutes === 0 ? 0 : minutes < 30 ? 1 : minutes < 60 ? 2 : minutes < 120 ? 3 : 4;
    const colors = ["var(--paper-soft)", "#f0d9b5", "#e8b978", "#e8a355", "#c47a2e"];
    return `<div class="heatmap-cell" title="${d}: ${minutes}m" style="background:${colors[intensity]}"></div>`;
  }).join("");
}

/* ---------------- Settings ---------------- */
async function renderSettingsView(container) {
  const user = Auth.getUser();
  container.innerHTML = `
    <h2 style="margin-bottom:16px">Settings</h2>
    <div class="card" style="padding:20px;max-width:480px;margin-bottom:16px">
      <h3 style="font-size:15px;margin-bottom:12px">Profile</h3>
      <div class="form-row"><label>Name</label><input id="set-name" value="${user ? escapeHtml(user.name) : ""}" /></div>
      <button class="btn btn-primary" id="save-profile-btn">Save changes</button>
    </div>
    <div class="card" style="padding:20px;max-width:480px;margin-bottom:16px">
      <h3 style="font-size:15px;margin-bottom:12px">Data</h3>
      <div style="display:flex;gap:10px;flex-wrap:wrap">
        <button class="btn btn-ghost" onclick="window.location.href='/api/export/csv'"><i data-lucide="download" width="15"></i> Export CSV</button>
        <button class="btn btn-ghost" onclick="window.location.href='/api/export/ics'"><i data-lucide="calendar-plus" width="15"></i> Export .ics</button>
        <button class="btn btn-ghost" onclick="window.location.href='/api/backup/export'"><i data-lucide="database-backup" width="15"></i> Full backup (JSON)</button>
      </div>
    </div>
    <div class="card" style="padding:20px;max-width:480px">
      <h3 style="font-size:15px;margin-bottom:6px">Accessibility</h3>
      <p style="color:var(--fg-dim);font-size:13px">StudySync respects your OS "reduce motion" setting, uses accessible color contrast, and is fully keyboard-navigable — try <span class="mono">Tab</span> and <span class="mono">⌘K</span>.</p>
    </div>`;
  refreshIcons();
  document.getElementById("save-profile-btn").addEventListener("click", async () => {
    const name = document.getElementById("set-name").value;
    const updated = await api("/api/auth/me", { method: "PATCH", body: { name } });
    Auth.setUser(updated);
    toast("Profile updated");
  });
}

document.addEventListener("DOMContentLoaded", bootApp);
window.addEventListener("hashchange", () => {
  const view = location.hash.replace("#", "");
  if (VIEWS.includes(view) && view !== activeView) switchView(view);
});
