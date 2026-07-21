function renderNav() {
  const nav = document.getElementById("nav");

  if (!state.user) {
    nav.innerHTML = "";
    nav.classList.remove("nav--visible");
    return;
  }

  nav.classList.add("nav--visible");
  const current = location.hash || "#/dashboard";
  const links = [
    { href: "#/dashboard", label: "Bosh sahifa" },
    { href: "#/chat", label: "AI Chat" },
    { href: "#/profile", label: "Profil" },
  ];

  nav.innerHTML = `
    <div class="nav__inner">
      <a class="nav__brand" href="#/dashboard">TravelAI</a>
      <nav class="nav__links">
        ${links
          .map(
            (l) =>
              `<a href="${l.href}" class="nav__link ${current.startsWith(l.href) ? "nav__link--active" : ""}">${l.label}</a>`
          )
          .join("")}
        <button type="button" class="nav__logout" id="nav-logout">Chiqish</button>
      </nav>
    </div>
  `;

  document.getElementById("nav-logout").addEventListener("click", async () => {
    try {
      await api.post("/auth/logout/");
    } catch (err) {
      // cookie tozalanmagan bo'lsa ham frontendda chiqib ketamiz
    }
    state.user = null;
    location.hash = "#/login";
  });
}

window.renderNav = renderNav;
