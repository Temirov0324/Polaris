window.pages = window.pages || {};

const TRIP_STATUS_LABELS = {
  planning: "Rejalashtirilmoqda",
  saving: "Jamg'arilmoqda",
  completed: "Yakunlandi",
  cancelled: "Bekor qilindi",
};

window.pages.profile = async function renderProfile() {
  const app = document.getElementById("app");
  app.innerHTML = '<div class="page"><p class="loading">Yuklanmoqda&hellip;</p></div>';

  let user;
  let trips;
  try {
    [user, trips] = await Promise.all([
      api.get("/auth/me/").then((r) => r.data),
      api.get("/trips/").then((r) => r.data),
    ]);
  } catch (err) {
    app.innerHTML = `<div class="page"><p class="error-text">Xatolik: ${escapeHtml(err.message)}</p></div>`;
    return;
  }

  function tripRow(trip) {
    const image = trip.destination_detail.image_url;
    return `
      <a class="trip-row" href="#/trips/${trip.id}/savings">
        ${image ? `<span class="trip-row__thumb" style="background-image:url('${escapeHtml(image)}')"></span>` : ""}
        <div class="trip-row__body">
          <strong>${escapeHtml(trip.destination_detail.city_uz)}</strong>
          <span>${formatDate(trip.start_date)}</span>
        </div>
        <span class="status-badge status-badge--${trip.status}">${TRIP_STATUS_LABELS[trip.status] || trip.status}</span>
      </a>
    `;
  }

  app.innerHTML = `
    <div class="page profile-page">
      <h2>Profil</h2>
      <form class="card" id="profile-form">
        <label>To'liq ism
          <input type="text" name="full_name" class="input" value="${escapeHtml(user.full_name)}" required />
        </label>
        <label>Email (bildirishnomalar uchun, ixtiyoriy)
          <input type="email" name="email" class="input" value="${escapeHtml(user.email)}" />
        </label>
        <label>Uy shahri
          <input type="text" name="home_city" class="input" value="${escapeHtml(user.home_city)}" />
        </label>
        <label>Valyuta
          <select name="currency" class="input">
            <option value="USD" ${user.currency === "USD" ? "selected" : ""}>USD</option>
            <option value="UZS" ${user.currency === "UZS" ? "selected" : ""}>UZS</option>
          </select>
        </label>
        <label class="checkbox-row"><input type="checkbox" name="notify_daily" ${user.notify_daily ? "checked" : ""} /> Kunlik eslatma</label>
        <label class="checkbox-row"><input type="checkbox" name="notify_weekly" ${user.notify_weekly ? "checked" : ""} /> Haftalik hisobot</label>
        <label class="checkbox-row"><input type="checkbox" name="notify_streak" ${user.notify_streak ? "checked" : ""} /> Streak ogohlantirishi</label>
        <label class="checkbox-row"><input type="checkbox" name="notify_price_drop" ${user.notify_price_drop ? "checked" : ""} /> Narx pasaysa xabar bering</label>
        <button type="submit" class="btn btn--primary btn--block">Saqlash</button>
      </form>

      <h3>Sayohatlar tarixi</h3>
      <div class="trip-history">
        ${trips.length === 0 ? '<p class="empty-hint">Hali sayohat yo\'q</p>' : trips.map(tripRow).join("")}
      </div>
    </div>
  `;

  document.getElementById("profile-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = e.target;
    const submitBtn = form.querySelector("button[type=submit]");
    submitBtn.disabled = true;
    try {
      const res = await api.patch("/auth/me/", {
        full_name: form.full_name.value.trim(),
        email: form.email.value.trim(),
        home_city: form.home_city.value.trim(),
        currency: form.currency.value,
        notify_daily: form.notify_daily.checked,
        notify_weekly: form.notify_weekly.checked,
        notify_streak: form.notify_streak.checked,
        notify_price_drop: form.notify_price_drop.checked,
      });
      state.user = res.data;
      showToast("Saqlandi!", "success");
    } catch (err) {
      showToast(err.message);
    } finally {
      submitBtn.disabled = false;
    }
  });
};
