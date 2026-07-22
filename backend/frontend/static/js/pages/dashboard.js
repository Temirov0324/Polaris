window.pages = window.pages || {};

/* This is the permanent "Bosh sahifa" landing view for logged-in users —
   it always shows the destination browser, regardless of whether the user
   already has an active goal. The goal/progress view lives at #/goal,
   reached only via the dedicated nav link — kirganda doim bir xil sahifa
   ko'rinishi kerak edi, oldin faol maqsad bo'lsa to'g'ridan-to'g'ri unga
   tushib qolardi. */
window.pages.dashboard = function renderDashboard() {
  const app = document.getElementById("app");
  app.innerHTML = `
    <div class="page home-page">
      <h2>Qayerga borishni xohlaysiz?</h2>
      <input type="search" id="home-dest-search" class="input" placeholder="Shahar qidirish..." />
      <div class="destination-grid" id="home-dest-grid"><p class="loading">Yuklanmoqda&hellip;</p></div>
    </div>
  `;

  async function loadDestinations(search) {
    const grid = document.getElementById("home-dest-grid");
    try {
      const query = search ? `?search=${encodeURIComponent(search)}` : "?popular=true";
      const res = await api.get(`/destinations/${query}`);
      const items = res.data;
      if (!items.length) {
        grid.innerHTML = '<p class="empty-hint">Hech narsa topilmadi</p>';
        return;
      }
      grid.innerHTML = items
        .map(
          (d) => `
        <button type="button" class="destination-card" data-id="${d.id}" data-city="${escapeHtml(d.city_uz)}" data-country="${escapeHtml(d.country_name)}">
          <div class="destination-card__image" style="${d.image_url ? `background-image:url('${escapeHtml(d.image_url)}')` : ""}">
            ${d.is_popular ? '<span class="badge-popular">🔥 Mashhur</span>' : ""}
          </div>
          <div class="destination-card__body">
            <strong>${escapeHtml(d.city_uz)}</strong>
            <span>${escapeHtml(d.country_name)}</span>
          </div>
        </button>
      `
        )
        .join("");
      grid.querySelectorAll(".destination-card").forEach((card) => {
        card.addEventListener("click", () => {
          window.pendingTripDestination = {
            id: Number(card.dataset.id),
            city_uz: card.dataset.city,
            country_name: card.dataset.country,
          };
          location.hash = "#/trips/new";
        });
      });
    } catch (err) {
      grid.innerHTML = `<p class="error-text">Xatolik: ${escapeHtml(err.message)}</p>`;
    }
  }

  loadDestinations();

  let debounceTimer;
  document.getElementById("home-dest-search").addEventListener("input", (e) => {
    clearTimeout(debounceTimer);
    const value = e.target.value.trim();
    debounceTimer = setTimeout(() => loadDestinations(value), 300);
  });
};
