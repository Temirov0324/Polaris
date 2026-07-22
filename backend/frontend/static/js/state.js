/* Small global store — no framework, just a plain object plus helpers. */

const state = {
  user: null,
  authChecked: false,
};

async function loadCurrentUser() {
  try {
    const res = await api.get("/auth/me/");
    state.user = res.data;
  } catch (err) {
    state.user = null;
  } finally {
    state.authChecked = true;
  }
  return state.user;
}

/* Static rate — good enough for V1 display purposes (not used for any real
   money movement, only formatting amounts that are always stored/computed
   in USD). Revisit if/when a live FX source is wired up. */
const USD_TO_UZS_RATE = 12700;

/* All amounts everywhere (budget, savings, target) are stored and computed
   in USD. This only converts how they're *displayed*, based on the logged-in
   user's chosen currency. */
function formatUsd(amountUsd) {
  const n = Number(amountUsd);
  if (state.user?.currency === "UZS") {
    const uzs = Math.round(n * USD_TO_UZS_RATE);
    return `${uzs.toLocaleString("en-US")} so'm`;
  }
  return `$${n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatDate(isoDate) {
  const d = new Date(isoDate);
  return d.toLocaleDateString("uz-UZ", { day: "numeric", month: "long", year: "numeric" });
}

/* Local calendar date as YYYY-MM-DD (NOT toISOString, which is UTC and can
   land on the wrong day for users east of UTC during their late-evening
   hours — e.g. Tashkent is UTC+5). */
function todayIso() {
  return new Date().toLocaleDateString("en-CA");
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

window.state = state;
window.loadCurrentUser = loadCurrentUser;
window.formatUsd = formatUsd;
window.formatDate = formatDate;
window.escapeHtml = escapeHtml;
window.todayIso = todayIso;
