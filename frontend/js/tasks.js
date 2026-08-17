/* ==========================================================================
   tasks.js — task list rendering, CRUD modal, filters, subtasks.
   Depends on app.js (api, toast, formatDate, etc.)
   ========================================================================== */

let currentTaskFilter = { status: null, subject_id: null, search: "" };
let cachedSubjects = [];

function renderTaskCard(task) {
  const isDone = task.status === "COMPLETED";
  const dueLabel = isDone ? `Completed` : timeUntil(task.due_date);
  return `
    <div class="card task-card ${isDone ? "completed" : ""}" data-task-id="${task.id}">
      <div class="check ${isDone ? "done" : ""}" data-action="toggle-complete">
        ${isDone ? '<i data-lucide="check" width="13"></i>' : ""}
      </div>
      <div style="flex:1;cursor:pointer" data-action="open-task">
        <div class="title">${escapeHtml(task.title)}</div>
        <div class="meta">
          <span>${task.subject_name || ""}</span>
          <span class="mono">${dueLabel} · ${formatDateTime(task.due_date)}</span>
          <span class="${priorityChipClass(task.priority)}">${task.priority}</span>
        </div>
      </div>
      <button class="icon-btn" data-action="delete-task" title="Delete">
        <i data-lucide="trash-2" width="15"></i>
      </button>
    </div>`;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str || "";
  return div.innerHTML;
}

async function loadSubjectsIntoCache() {
  cachedSubjects = await api("/api/subjects");
  return cachedSubjects;
}

function subjectName(id) {
  const s = cachedSubjects.find(s => s.id === id);
  return s ? s.name : "";
}

async function renderTasksView(container) {
  container.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:10px">
      <h2>Tasks</h2>
      <button class="btn btn-primary" id="new-task-btn"><i data-lucide="plus" width="16"></i> New task</button>
    </div>
    <div class="tab-row" id="task-status-tabs">
      <div class="tab-item active" data-status="">All</div>
      <div class="tab-item" data-status="TODO">To do</div>
      <div class="tab-item" data-status="IN_PROGRESS">In progress</div>
      <div class="tab-item" data-status="COMPLETED">Completed</div>
      <div class="tab-item" data-status="OVERDUE">Overdue</div>
    </div>
    <div id="task-list"></div>
  `;
  refreshIcons();

  container.querySelectorAll("#task-status-tabs .tab-item").forEach(tab => {
    tab.addEventListener("click", () => {
      container.querySelectorAll("#task-status-tabs .tab-item").forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      currentTaskFilter.status = tab.dataset.status || null;
      loadTaskList();
    });
  });

  document.getElementById("new-task-btn").addEventListener("click", () => openTaskModal());

  await loadSubjectsIntoCache();
  await loadTaskList();
}

async function loadTaskList() {
  const listEl = document.getElementById("task-list");
  if (!listEl) return;
  listEl.innerHTML = `<div class="skeleton" style="height:60px;margin-bottom:8px"></div>`.repeat(3);

  const params = new URLSearchParams();
  if (currentTaskFilter.status) params.set("status", currentTaskFilter.status);
  if (currentTaskFilter.subject_id) params.set("subject_id", currentTaskFilter.subject_id);
  if (currentTaskFilter.search) params.set("search", currentTaskFilter.search);

  const tasks = await api(`/api/tasks?${params.toString()}`);
  tasks.forEach(t => { t.subject_name = subjectName(t.subject_id); });

  if (!tasks.length) {
    listEl.innerHTML = `<div class="empty-state card"><i data-lucide="check-circle" width="28"></i><p>No tasks here. Add one to get started.</p></div>`;
    refreshIcons();
    return;
  }

  listEl.innerHTML = tasks.map(renderTaskCard).join("");
  refreshIcons();

  listEl.querySelectorAll(".task-card").forEach(card => {
    const taskId = Number(card.dataset.taskId);
    card.querySelector('[data-action="toggle-complete"]').addEventListener("click", async (e) => {
      e.stopPropagation();
      try {
        await api(`/api/tasks/${taskId}/complete`, { method: "POST" });
        toast("Task completed. +10 XP");
        loadTaskList();
        refreshSidebarStats();
      } catch (err) { toast(err.message, "error"); }
    });
    card.querySelector('[data-action="delete-task"]').addEventListener("click", async (e) => {
      e.stopPropagation();
      if (!confirm("Delete this task?")) return;
      await api(`/api/tasks/${taskId}`, { method: "DELETE" });
      toast("Task deleted");
      loadTaskList();
    });
    card.querySelector('[data-action="open-task"]').addEventListener("click", async () => {
      const task = await api(`/api/tasks/${taskId}`);
      openTaskModal(task);
    });
  });
}

function openTaskModal(task = null) {
  const isEdit = !!task;
  const backdrop = document.createElement("div");
  backdrop.className = "modal-backdrop";
  backdrop.innerHTML = `
    <div class="modal">
      <h3>${isEdit ? "Edit task" : "New task"}</h3>
      <form id="task-form">
        <div class="form-row"><label>Title</label><input id="tf-title" required value="${task ? escapeHtml(task.title) : ""}" /></div>
        <div class="form-row"><label>Description</label><textarea id="tf-desc" rows="2">${task ? escapeHtml(task.description || "") : ""}</textarea></div>
        <div class="form-grid">
          <div class="form-row">
            <label>Subject</label>
            <select id="tf-subject">${cachedSubjects.map(s => `<option value="${s.id}" ${task && task.subject_id === s.id ? "selected" : ""}>${escapeHtml(s.name)}</option>`).join("")}</select>
          </div>
          <div class="form-row">
            <label>Type</label>
            <select id="tf-type">
              ${["assignment", "project", "lab", "homework", "other"].map(t => `<option value="${t}" ${task && task.type === t ? "selected" : ""}>${t}</option>`).join("")}
            </select>
          </div>
        </div>
        <div class="form-grid">
          <div class="form-row">
            <label>Priority</label>
            <select id="tf-priority">
              ${["LOW", "MEDIUM", "HIGH", "URGENT"].map(p => `<option value="${p}" ${task && task.priority === p ? "selected" : ""}>${p}</option>`).join("")}
            </select>
          </div>
          <div class="form-row"><label>Estimated hours</label><input id="tf-hours" type="number" min="0" step="0.5" value="${task ? task.estimated_hours : 1}" /></div>
        </div>
        <div class="form-row"><label>Due date &amp; time</label><input id="tf-due" type="datetime-local" required value="${task ? toLocalInputValue(task.due_date) : ""}" /></div>
        <div class="form-row">
          <label>Repeats</label>
          <select id="tf-recurrence">
            <option value="">Does not repeat</option>
            <option value="DAILY" ${task && task.recurrence_rule === "DAILY" ? "selected" : ""}>Daily</option>
            <option value="WEEKLY" ${task && task.recurrence_rule === "WEEKLY" ? "selected" : ""}>Weekly</option>
            <option value="MONTHLY" ${task && task.recurrence_rule === "MONTHLY" ? "selected" : ""}>Monthly</option>
          </select>
        </div>
        <div style="display:flex;gap:10px;margin-top:16px">
          <button type="submit" class="btn btn-primary" style="flex:1;justify-content:center">${isEdit ? "Save changes" : "Create task"}</button>
          <button type="button" class="btn btn-ghost" id="tf-cancel">Cancel</button>
        </div>
      </form>
    </div>`;
  document.body.appendChild(backdrop);
  backdrop.addEventListener("click", (e) => { if (e.target === backdrop) backdrop.remove(); });
  document.getElementById("tf-cancel").addEventListener("click", () => backdrop.remove());

  document.getElementById("task-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      title: document.getElementById("tf-title").value,
      description: document.getElementById("tf-desc").value,
      subject_id: Number(document.getElementById("tf-subject").value),
      type: document.getElementById("tf-type").value,
      priority: document.getElementById("tf-priority").value,
      estimated_hours: Number(document.getElementById("tf-hours").value) || 1,
      due_date: new Date(document.getElementById("tf-due").value).toISOString(),
      recurrence_rule: document.getElementById("tf-recurrence").value || null,
    };
    try {
      if (isEdit) {
        await api(`/api/tasks/${task.id}`, { method: "PATCH", body: payload });
        toast("Task updated");
      } else {
        await api("/api/tasks", { method: "POST", body: payload });
        toast("Task created");
      }
      backdrop.remove();
      loadTaskList();
    } catch (err) {
      toast(err.message, "error");
    }
  });
}

function toLocalInputValue(iso) {
  const d = new Date(iso);
  const pad = n => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
