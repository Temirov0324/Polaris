window.pages = window.pages || {};

window.pages.tripWizard = function renderTripWizard() {
  const wizard = {
    step: 1,
    data: {
      destination: null,
      start_date: "",
      duration_days: 5,
      travelers_count: 1,
      style: "standard",
    },
  };
  renderWizardStep(wizard);
};

function renderWizardStep(wizard) {
  const app = document.getElementById("app");
  app.innerHTML = `
    <div class="page wizard">
      <div class="wizard__progress">
        ${[1, 2, 3, 4, 5]
          .map((n) => `<span class="wizard__dot ${n <= wizard.step ? "wizard__dot--active" : ""}"></span>`)
          .join("")}
      </div>
      <div id="wizard-step"></div>
    </div>
  `;
  const stepEl = document.getElementById("wizard-step");

  if (wizard.step === 1) renderWizardDestination(stepEl, wizard);
  else if (wizard.step === 2) renderWizardDates(stepEl, wizard);
  else if (wizard.step === 3) renderWizardTravelers(stepEl, wizard);
  else if (wizard.step === 4) renderWizardStyle(stepEl, wizard);
  else renderWizardResult(stepEl, wizard);
}

function renderWizardDestination(el, wizard) {
  el.innerHTML = `
    <h2>Qayerga borasiz?</h2>
    <input type="search" id="dest-search" class="input" placeholder="Shahar qidirish..." />
    <div class="destination-grid" id="dest-grid"><p class="loading">Yuklanmoqda&hellip;</p></div>
  `;

  async function loadDestinations(search) {
    const grid = document.getElementById("dest-grid");
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
          wizard.data.destination = {
            id: Number(card.dataset.id),
            city_uz: card.dataset.city,
            country_name: card.dataset.country,
          };
          wizard.step = 2;
          renderWizardStep(wizard);
        });
      });
    } catch (err) {
      grid.innerHTML = `<p class="error-text">Xatolik: ${escapeHtml(err.message)}</p>`;
    }
  }

  loadDestinations();

  let debounceTimer;
  document.getElementById("dest-search").addEventListener("input", (e) => {
    clearTimeout(debounceTimer);
    const value = e.target.value.trim();
    debounceTimer = setTimeout(() => loadDestinations(value), 300);
  });
}

function renderWizardDates(el, wizard) {
  const minDate = todayIso();
  el.innerHTML = `
    <h2>Sana va davomiylik</h2>
    <label>Ketish sanasi
      <input type="date" id="start-date" class="input" min="${minDate}" value="${wizard.data.start_date}" required />
    </label>
    <label>Necha kun
      <input type="number" id="duration" class="input" min="1" max="60" value="${wizard.data.duration_days}" required />
    </label>
    <div class="wizard__nav">
      <button type="button" class="btn btn--ghost" id="back-btn">Orqaga</button>
      <button type="button" class="btn btn--primary" id="next-btn">Keyingisi</button>
    </div>
  `;

  document.getElementById("back-btn").addEventListener("click", () => {
    wizard.step = 1;
    renderWizardStep(wizard);
  });
  document.getElementById("next-btn").addEventListener("click", () => {
    const startDate = document.getElementById("start-date").value;
    const duration = Number(document.getElementById("duration").value);
    if (!startDate || !duration || duration < 1) {
      showToast("Sana va davomiylikni to'g'ri kiriting");
      return;
    }
    wizard.data.start_date = startDate;
    wizard.data.duration_days = duration;
    wizard.step = 3;
    renderWizardStep(wizard);
  });
}

function renderWizardTravelers(el, wizard) {
  el.innerHTML = `
    <h2>Necha kishi boradi?</h2>
    <div class="stepper">
      <button type="button" class="stepper__btn" id="dec-btn">−</button>
      <span class="stepper__value" id="travelers-value">${wizard.data.travelers_count}</span>
      <button type="button" class="stepper__btn" id="inc-btn">+</button>
    </div>
    <div class="wizard__nav">
      <button type="button" class="btn btn--ghost" id="back-btn">Orqaga</button>
      <button type="button" class="btn btn--primary" id="next-btn">Keyingisi</button>
    </div>
  `;

  const valueEl = document.getElementById("travelers-value");
  document.getElementById("dec-btn").addEventListener("click", () => {
    wizard.data.travelers_count = Math.max(1, wizard.data.travelers_count - 1);
    valueEl.textContent = wizard.data.travelers_count;
  });
  document.getElementById("inc-btn").addEventListener("click", () => {
    wizard.data.travelers_count = Math.min(10, wizard.data.travelers_count + 1);
    valueEl.textContent = wizard.data.travelers_count;
  });
  document.getElementById("back-btn").addEventListener("click", () => {
    wizard.step = 2;
    renderWizardStep(wizard);
  });
  document.getElementById("next-btn").addEventListener("click", () => {
    wizard.step = 4;
    renderWizardStep(wizard);
  });
}

function renderWizardStyle(el, wizard) {
  const styles = [
    { key: "econom", icon: "💰", label: "Econom", desc: "Tejamkor, byudjetli sayohat" },
    { key: "standard", icon: "⚖️", label: "Standard", desc: "Qulay muvozanat" },
    { key: "comfort", icon: "✨", label: "Comfort", desc: "Yuqori qulaylik" },
  ];

  el.innerHTML = `
    <h2>Sayohat uslubi</h2>
    <div class="style-grid">
      ${styles
        .map(
          (s) => `
        <button type="button" class="style-card ${wizard.data.style === s.key ? "style-card--active" : ""}" data-style="${s.key}">
          <span class="style-card__icon">${s.icon}</span>
          <strong>${s.label}</strong>
          <span>${s.desc}</span>
        </button>
      `
        )
        .join("")}
    </div>
    <div class="wizard__nav">
      <button type="button" class="btn btn--ghost" id="back-btn">Orqaga</button>
      <button type="button" class="btn btn--primary" id="next-btn">Hisoblash</button>
    </div>
  `;

  el.querySelectorAll(".style-card").forEach((card) => {
    card.addEventListener("click", () => {
      wizard.data.style = card.dataset.style;
      el.querySelectorAll(".style-card").forEach((c) => c.classList.remove("style-card--active"));
      card.classList.add("style-card--active");
    });
  });
  document.getElementById("back-btn").addEventListener("click", () => {
    wizard.step = 3;
    renderWizardStep(wizard);
  });
  document.getElementById("next-btn").addEventListener("click", () => {
    wizard.step = 5;
    renderWizardStep(wizard);
  });
}

const BREAKDOWN_LABELS = {
  flight: "Chipta",
  accommodation: "Turar joy",
  food: "Ovqat",
  transport: "Transport",
  activities: "Ko'ngilochar",
  visa: "Viza",
  insurance: "Sug'urta",
  reserve: "Zaxira (15%)",
};

async function renderWizardResult(el, wizard) {
  el.innerHTML = '<p class="loading">Hisoblanmoqda&hellip;</p>';

  let est;
  try {
    const res = await api.post("/trips/estimate/", {
      destination: wizard.data.destination.id,
      start_date: wizard.data.start_date,
      duration_days: wizard.data.duration_days,
      travelers_count: wizard.data.travelers_count,
      style: wizard.data.style,
    });
    est = res.data;
  } catch (err) {
    el.innerHTML = `
      <p class="error-text">Xatolik: ${escapeHtml(err.message)}</p>
      <button class="btn btn--ghost" id="back-btn">Orqaga</button>
    `;
    document.getElementById("back-btn").addEventListener("click", () => {
      wizard.step = 4;
      renderWizardStep(wizard);
    });
    return;
  }

  const suggestedTarget = Math.round((Number(est.budget_min) + Number(est.budget_max)) / 2);

  el.innerHTML = `
    ${
      est.destination.image_url
        ? `<div class="result-hero" style="background-image:url('${escapeHtml(est.destination.image_url)}')"></div>`
        : ""
    }
    <h2>${escapeHtml(wizard.data.destination.city_uz)} — byudjet</h2>
    ${est.confidence === "low" ? '<p class="confidence-hint">Bu taxminiy hisob — ma\'lumot ishonchliligi past.</p>' : ""}
    <div class="budget-range card">
      <span class="budget-range__value">${formatUsd(est.budget_min)} – ${formatUsd(est.budget_max)}</span>
      <span class="budget-range__hint">${wizard.data.duration_days} kun &middot; ${wizard.data.travelers_count} kishi</span>
    </div>
    <div class="breakdown-list card">
      ${Object.entries(BREAKDOWN_LABELS)
        .map(
          ([key, label]) => `
        <div class="breakdown-row">
          <span>${label}</span>
          <span>${formatUsd(est.breakdown[key])}</span>
        </div>
      `
        )
        .join("")}
    </div>
    <form id="target-form">
      <label>Maqsad summasi (USD)
        <input type="number" name="target_amount" class="input" min="1" step="1" value="${suggestedTarget}" required />
      </label>
      <div class="wizard__nav">
        <button type="button" class="btn btn--ghost" id="back-btn">Orqaga</button>
        <button type="submit" class="btn btn--primary">Maqsad qilib belgilash</button>
      </div>
    </form>
  `;

  document.getElementById("back-btn").addEventListener("click", () => {
    wizard.step = 4;
    renderWizardStep(wizard);
  });

  document.getElementById("target-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const targetAmount = Number(e.target.target_amount.value);
    const submitBtn = e.target.querySelector("button[type=submit]");
    submitBtn.disabled = true;
    try {
      await api.post("/trips/", {
        destination: wizard.data.destination.id,
        start_date: wizard.data.start_date,
        duration_days: wizard.data.duration_days,
        travelers_count: wizard.data.travelers_count,
        style: wizard.data.style,
        target_amount: targetAmount,
      });
      showToast("Sayohat rejasi yaratildi!", "success");
      location.hash = "#/dashboard";
    } catch (err) {
      showToast(err.message);
      submitBtn.disabled = false;
    }
  });
}
