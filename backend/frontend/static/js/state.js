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

function formatUsd(amount) {
  const n = Number(amount);
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
