window.pages = window.pages || {};

window.pages.login = function renderLogin() {
  document.getElementById("app").innerHTML = `
    <div class="auth-page">
      <form class="auth-card card" id="login-form">
        <h1>Kirish</h1>
        <label>Telefon raqam
          <input type="tel" name="phone" class="input" placeholder="+998901234567" required />
        </label>
        <label>Parol
          <input type="password" name="password" class="input" required minlength="8" />
        </label>
        <button class="btn btn--primary btn--block" type="submit">Kirish</button>
        <p class="auth-card__switch">Hisobingiz yo'qmi? <a href="#/register">Ro'yxatdan o'tish</a></p>
      </form>
    </div>
  `;

  document.getElementById("login-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = e.target;
    const submitBtn = form.querySelector("button[type=submit]");
    submitBtn.disabled = true;
    try {
      const res = await api.post("/auth/login/", {
        phone: form.phone.value.trim(),
        password: form.password.value,
      });
      state.user = res.data;
      location.hash = "#/dashboard";
    } catch (err) {
      showToast(err.message);
    } finally {
      submitBtn.disabled = false;
    }
  });
};

window.pages.register = function renderRegister() {
  document.getElementById("app").innerHTML = `
    <div class="auth-page">
      <form class="auth-card card" id="register-form">
        <h1>Ro'yxatdan o'tish</h1>
        <label>To'liq ism
          <input type="text" name="full_name" class="input" required />
        </label>
        <label>Telefon raqam
          <input type="tel" name="phone" class="input" placeholder="+998901234567" pattern="\\+998\\d{9}" required />
        </label>
        <label>Parol
          <input type="password" name="password" class="input" required minlength="8" />
        </label>
        <button class="btn btn--primary btn--block" type="submit">Ro'yxatdan o'tish</button>
        <p class="auth-card__switch">Hisobingiz bormi? <a href="#/login">Kirish</a></p>
      </form>
    </div>
  `;

  document.getElementById("register-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = e.target;
    const submitBtn = form.querySelector("button[type=submit]");
    submitBtn.disabled = true;
    try {
      const res = await api.post("/auth/register/", {
        full_name: form.full_name.value.trim(),
        phone: form.phone.value.trim(),
        password: form.password.value,
      });
      state.user = res.data;
      location.hash = "#/dashboard";
    } catch (err) {
      showToast(err.message);
    } finally {
      submitBtn.disabled = false;
    }
  });
};
