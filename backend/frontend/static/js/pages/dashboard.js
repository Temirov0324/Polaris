window.pages = window.pages || {};

window.pages.dashboard = async function renderDashboard() {
  const app = document.getElementById("app");
  app.innerHTML = '<div class="page"><p class="loading">Yuklanmoqda&hellip;</p></div>';

  const tripsRes = await api.get("/trips/");
  const trips = tripsRes.data;
  const activeTrip = trips.find((t) => ["planning", "saving"].includes(t.status));

  if (!activeTrip) {
    app.innerHTML = `
      <div class="page page--empty">
        <div class="empty-state card">
          <h2>Hali sayohat rejangiz yo'q</h2>
          <p>3 ta qadam — yo'nalish, sana, uslub — va biz byudjetingizni hisoblab beramiz.</p>
          <a class="btn btn--primary btn--block" href="#/trips/new">Sayohat rejasi yaratish</a>
          <p class="empty-hint empty-hint--spaced">yoki <a href="#/chat">AI chatdan so'rang</a> — masalan "Turkiyaga 7 kunga qancha kerak?"</p>
        </div>
      </div>
    `;
    return;
  }

  const [planRes, statsRes] = await Promise.all([
    api.get(`/trips/${activeTrip.id}/plan/`),
    api.get(`/trips/${activeTrip.id}/savings/stats/`),
  ]);
  const plan = planRes.data;
  const stats = statsRes.data;
  const hasTarget = activeTrip.target_amount != null && plan.progress_pct !== undefined;

  const daysLeft = Math.max(0, Math.ceil((new Date(activeTrip.start_date) - new Date()) / 86400000));

  const heroImage = activeTrip.destination_detail.image_url;

  app.innerHTML = `
    <div class="page dashboard">
      ${heroImage ? `<div class="dashboard__banner" style="background-image:url('${escapeHtml(heroImage)}')"></div>` : ""}
      <div class="dashboard__hero card">
        <div class="dashboard__ring">
          <canvas id="progress-ring" width="140" height="140"></canvas>
          <div class="dashboard__ring-label">
            <strong>${hasTarget ? Math.round(plan.progress_pct) : 0}%</strong>
            <span>bajarildi</span>
          </div>
        </div>
        <div class="dashboard__info">
          <h2>${escapeHtml(activeTrip.destination_detail.city_uz)}</h2>
          <p>${daysLeft} kun qoldi &middot; ${escapeHtml(activeTrip.destination_detail.country_name)}</p>
          <div class="dashboard__streak">🔥 ${stats.streak} kun</div>
        </div>
      </div>

      ${
        hasTarget
          ? `
        <div class="dashboard__stats">
          <div class="stat-tile"><span>Yig'ilgan</span><strong>${formatUsd(plan.saved)}</strong></div>
          <div class="stat-tile"><span>Maqsad</span><strong>${formatUsd(activeTrip.target_amount)}</strong></div>
          <div class="stat-tile"><span>Qolgan</span><strong>${formatUsd(plan.remaining)}</strong></div>
        </div>
        <p class="dashboard__hint">Kuniga taxminan <strong>${formatUsd(plan.per_day)}</strong> jamg'aring.</p>
      `
          : `
        <p class="dashboard__hint">Byudjet diapazoni: ${formatUsd(activeTrip.budget_min)} – ${formatUsd(activeTrip.budget_max)}.</p>
      `
      }

      <button class="btn btn--primary btn--block btn--large" id="add-saving-btn">Bugun jamg'ardim</button>
      <a class="btn btn--ghost btn--block" href="#/trips/${activeTrip.id}/savings">Jamg'arish tarixi</a>

      <div class="dashboard__trip-actions">
        <button type="button" class="link-btn" id="edit-trip-btn">Maqsadni tahrirlash</button>
        <button type="button" class="link-btn link-btn--danger" id="cancel-trip-btn">Sayohatni bekor qilish</button>
      </div>
    </div>
  `;

  drawProgressRing(document.getElementById("progress-ring"), hasTarget ? plan.progress_pct : 0);

  document.getElementById("add-saving-btn").addEventListener("click", () => {
    openSavingModal(activeTrip.id, { onSaved: () => window.pages.dashboard() });
  });

  document.getElementById("edit-trip-btn").addEventListener("click", () => {
    openTripEditModal(activeTrip, { onSaved: () => window.pages.dashboard() });
  });

  document.getElementById("cancel-trip-btn").addEventListener("click", async () => {
    if (!confirm("Bu sayohatni bekor qilishni tasdiqlaysizmi?")) return;
    try {
      await api.patch(`/trips/${activeTrip.id}/`, { status: "cancelled" });
      showToast("Sayohat bekor qilindi", "success");
      window.pages.dashboard();
    } catch (err) {
      showToast(err.message);
    }
  });
};
