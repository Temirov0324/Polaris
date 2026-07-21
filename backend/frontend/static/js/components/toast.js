function showToast(message, type = "error") {
  const root = document.getElementById("toast-root");
  const el = document.createElement("div");
  el.className = `toast toast--${type}`;
  el.textContent = message;
  root.appendChild(el);

  requestAnimationFrame(() => el.classList.add("toast--visible"));
  setTimeout(() => {
    el.classList.remove("toast--visible");
    setTimeout(() => el.remove(), 250);
  }, 3500);
}

window.showToast = showToast;
