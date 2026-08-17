/* ==========================================================================
   calendar.js — FullCalendar month/week/day view of tasks, exams,
   and study sessions.
   ========================================================================== */

let calendarInstance = null;

async function renderCalendarView(container) {
  container.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <h2>Calendar</h2>
      <div style="display:flex;gap:14px;font-size:12px;color:var(--fg-dim)">
        <span>📝 Tasks</span><span>🧪 Exams</span><span>📖 Study sessions</span>
      </div>
    </div>
    <div class="card" style="padding:18px" id="calendar-el"></div>
  `;

  const el = document.getElementById("calendar-el");
  calendarInstance = new FullCalendar.Calendar(el, {
    initialView: "dayGridMonth",
    headerToolbar: { left: "prev,next today", center: "title", right: "dayGridMonth,timeGridWeek,timeGridDay" },
    height: "auto",
    events: async (info, success, failure) => {
      try {
        const params = new URLSearchParams({ start: info.startStr, end: info.endStr });
        const events = await api(`/api/calendar/events?${params.toString()}`);
        success(events);
      } catch (err) {
        failure(err);
      }
    },
    eventClick: (info) => {
      const { type, ref_id } = info.event.extendedProps;
      toast(`${info.event.title} — ${type.replace("_", " ")}`);
    },
  });
  calendarInstance.render();
}
