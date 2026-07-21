window.pages = window.pages || {};

window.pages.savings = async function renderSavings(tripId) {
  const app = document.getElementById("app");
  app.innerHTML = '<div class="page"><p class="loading">Yuklanmoqda&hellip;</p></div>';

  let trip;
  let entries;
  let stats;
  try {
    [trip, entries, stats] = await Promise.all([
      api.get(`/trips/${tripId}/`).then((r) => r.data),
      api.get(`/trips/${tripId}/savings/`).then((r) => r.data),
      api.get(`/trips/${tripId}/savings/stats/`).then((r) => r.data),
    ]);
  } catch (err) {
    app.innerHTML = `<div class="page"><p class="error-text">Xatolik: ${escapeHtml(err.message)}</p></div>`;
    return;
  }

  function entryRow(entry) {
    return `
      <div class="entry-row">
        <div>
          <strong>${formatUsd(entry.amount)}</strong>
          <span>${formatDate(entry.date)}</span>
          ${entry.note ? `<p class="entry-row__note">${escapeHtml(entry.note)}</p>` : ""}
        </div>
        <button type="button" class="entry-row__delete" data-id="${entry.id}" aria-label="O'chirish">✕</button>
      </div>
    `;
  }

  function renderCalendar() {
    const grid = document.getElementById("calendar-grid");
    const today = new Date();
    const year = today.getFullYear();
    const month = today.getMonth();
    const firstWeekday = (new Date(year, month, 1).getDay() + 6) % 7; // Dushanba=0
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const savedDates = new Set(entries.map((e) => e.date));
    const todayStr = todayIso();

    let cells = "";
    for (let i = 0; i < firstWeekday; i++) {
      cells += '<span class="calendar-cell calendar-cell--empty"></span>';
    }
    for (let day = 1; day <= daysInMonth; day++) {
      const iso = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
      const classes = ["calendar-cell"];
      if (savedDates.has(iso)) classes.push("calendar-cell--saved");
      if (iso === todayStr) classes.push("calendar-cell--today");
      cells += `<span class="${classes.join(" ")}">${day}</span>`;
    }
    grid.innerHTML = cells;
  }

  function render() {
    app.innerHTML = `
      <div class="page savings-page">
        ${
          trip.destination_detail.image_url
            ? `<div class="dashboard__banner dashboard__banner--small" style="background-image:url('${escapeHtml(trip.destination_detail.image_url)}')"></div>`
            : ""
        }
        <h2>${escapeHtml(trip.destination_detail.city_uz)} — jamg'arish</h2>
        <div class="savings-page__streak">🔥 ${stats.streak} kun ketma-ket</div>

        <div class="card chart-card">
          <h3>Bu hafta</h3>
          <canvas id="weekly-chart" width="320" height="140"></canvas>
        </div>

        <div class="card calendar-card">
          <h3>${new Date().toLocaleDateString("uz-UZ", { month: "long", year: "numeric" })}</h3>
          <div class="calendar-grid" id="calendar-grid"></div>
        </div>

        <button type="button" class="btn btn--primary btn--block btn--large" id="add-btn">+ Jamg'arish qo'shish</button>

        <div class="entries-list">
          <h3>Yozuvlar</h3>
          ${entries.length === 0 ? '<p class="empty-hint">Hali yozuv yo\'q</p>' : entries.map(entryRow).join("")}
        </div>
      </div>
    `;

    drawBarChart(
      document.getElementById("weekly-chart"),
      stats.weekly.map((w) => ({
        label: new Date(w.date).toLocaleDateString("uz-UZ", { weekday: "short" }),
        value: Number(w.amount),
      }))
    );

    renderCalendar();

    document.getElementById("add-btn").addEventListener("click", () => {
      openSavingModal(tripId, { onSaved: reload });
    });

    app.querySelectorAll(".entry-row__delete").forEach((btn) => {
      btn.addEventListener("click", async () => {
        if (!confirm("O'chirishni tasdiqlaysizmi?")) return;
        try {
          await api.delete(`/savings/${btn.dataset.id}/`);
          showToast("O'chirildi", "success");
          reload();
        } catch (err) {
          showToast(err.message);
        }
      });
    });
  }

  async function reload() {
    [entries, stats] = await Promise.all([
      api.get(`/trips/${tripId}/savings/`).then((r) => r.data),
      api.get(`/trips/${tripId}/savings/stats/`).then((r) => r.data),
    ]);
    render();
  }

  render();
};
