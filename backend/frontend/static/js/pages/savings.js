window.pages = window.pages || {};

window.pages.savings = async function renderSavings(tripId) {
  const app = document.getElementById("app");
  app.innerHTML = '<div class="page"><p class="loading">Yuklanmoqda&hellip;</p></div>';

  let trip;
  let entries;
  let stats;
  let members;
  try {
    [trip, entries, stats, members] = await Promise.all([
      api.get(`/trips/${tripId}/`).then((r) => r.data),
      api.get(`/trips/${tripId}/savings/`).then((r) => r.data),
      api.get(`/trips/${tripId}/savings/stats/`).then((r) => r.data),
      api.get(`/trips/${tripId}/members/`).then((r) => r.data),
    ]);
  } catch (err) {
    app.innerHTML = `<div class="page"><p class="error-text">Xatolik: ${escapeHtml(err.message)}</p></div>`;
    return;
  }

  const isOwner = members.find((m) => m.is_owner)?.id === state.user.id;

  function entryRow(entry) {
    return `
      <div class="entry-row">
        <div>
          <strong>${formatUsd(entry.amount)}</strong>
          <span>${formatDate(entry.date)}${entry.user_name ? ` &middot; ${escapeHtml(entry.user_name)}` : ""}</span>
          ${entry.note ? `<p class="entry-row__note">${escapeHtml(entry.note)}</p>` : ""}
        </div>
        <button type="button" class="entry-row__delete" data-id="${entry.id}" aria-label="O'chirish">✕</button>
      </div>
    `;
  }

  function memberRow(m) {
    return `
      <div class="member-row">
        <div>
          <strong>${escapeHtml(m.full_name)}${m.is_owner ? " (egasi)" : ""}</strong>
          <span>${formatUsd(m.total_saved)} jamg'ardi</span>
        </div>
        ${isOwner && !m.is_owner ? `<button type="button" class="entry-row__delete" data-user-id="${m.id}" aria-label="Olib tashlash">✕</button>` : ""}
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

        <div class="card members-card">
          <h3>A'zolar${members.length > 1 ? ` (${members.length})` : ""}</h3>
          <div class="member-list">${members.map(memberRow).join("")}</div>
          ${
            isOwner
              ? `
            <form id="add-member-form" class="add-member-form">
              <input type="tel" name="phone" class="input" placeholder="+998901234567" required />
              <button type="submit" class="btn btn--ghost">A'zo qo'shish</button>
            </form>
          `
              : ""
          }
        </div>

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

    app.querySelectorAll(".entry-row__delete[data-id]").forEach((btn) => {
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

    app.querySelectorAll(".entry-row__delete[data-user-id]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        if (!confirm("Bu a'zoni olib tashlashni tasdiqlaysizmi?")) return;
        try {
          await api.delete(`/trips/${tripId}/members/${btn.dataset.userId}/`);
          showToast("A'zo olib tashlandi", "success");
          reload();
        } catch (err) {
          showToast(err.message);
        }
      });
    });

    const addMemberForm = document.getElementById("add-member-form");
    if (addMemberForm) {
      addMemberForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const submitBtn = e.target.querySelector("button[type=submit]");
        submitBtn.disabled = true;
        try {
          await api.post(`/trips/${tripId}/members/`, { phone: e.target.phone.value.trim() });
          showToast("A'zo qo'shildi", "success");
          reload();
        } catch (err) {
          showToast(err.message);
        } finally {
          submitBtn.disabled = false;
        }
      });
    }
  }

  async function reload() {
    [entries, stats, members] = await Promise.all([
      api.get(`/trips/${tripId}/savings/`).then((r) => r.data),
      api.get(`/trips/${tripId}/savings/stats/`).then((r) => r.data),
      api.get(`/trips/${tripId}/members/`).then((r) => r.data),
    ]);
    render();
  }

  render();
};
