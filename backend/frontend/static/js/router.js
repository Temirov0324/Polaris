const routes = [
  { pattern: /^#\/?$/, page: () => window.pages.landing(), public: true },
  { pattern: /^#\/login\/?$/, page: () => window.pages.login(), public: true },
  { pattern: /^#\/register\/?$/, page: () => window.pages.register(), public: true },
  { pattern: /^#\/password-reset\/?$/, page: () => window.pages.passwordReset(), public: true },
  { pattern: /^#\/dashboard\/?$/, page: () => window.pages.dashboard() },
  { pattern: /^#\/trips\/new\/?$/, page: () => window.pages.tripWizard() },
  { pattern: /^#\/trips\/(\d+)\/savings\/?$/, page: (m) => window.pages.savings(Number(m[1])) },
  { pattern: /^#\/chat\/?$/, page: () => window.pages.chat() },
  { pattern: /^#\/profile\/?$/, page: () => window.pages.profile() },
];

const PUBLIC_ONLY_PREFIXES = ["#/login", "#/register", "#/password-reset"];

async function router() {
  if (!state.authChecked) {
    await loadCurrentUser();
  }

  const hash = location.hash || "#/";
  const app = document.getElementById("app");

  for (const route of routes) {
    const match = hash.match(route.pattern);
    if (!match) continue;

    if (!route.public && !state.user) {
      location.hash = "#/login";
      return;
    }

    if (state.user && (hash === "#/" || hash === "" || PUBLIC_ONLY_PREFIXES.some((p) => hash.startsWith(p)))) {
      location.hash = "#/dashboard";
      return;
    }

    renderNav();
    app.innerHTML = '<div class="page"><p class="loading">Yuklanmoqda&hellip;</p></div>';
    try {
      await route.page(match);
    } catch (err) {
      console.error(err);
      app.innerHTML = `<div class="page"><p class="error-text">Xatolik yuz berdi: ${escapeHtml(err.message || "")}</p></div>`;
    }
    return;
  }

  renderNav();
  app.innerHTML = `
    <div class="page">
      <h2>Sahifa topilmadi</h2>
      <a class="btn btn--primary" href="#/dashboard">Bosh sahifaga qaytish</a>
    </div>
  `;
}

window.addEventListener("hashchange", router);
window.addEventListener("DOMContentLoaded", router);
