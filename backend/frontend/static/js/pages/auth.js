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
        <p class="auth-card__switch"><a href="#/password-reset">Parolni unutdingizmi?</a></p>
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
  let email = "";

  function renderForm() {
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
          <label>Email
            <input type="email" name="email" class="input" placeholder="siz@example.com" required />
          </label>
          <label>Parol
            <input type="password" name="password" class="input" required minlength="8" />
          </label>
          <button class="btn btn--primary btn--block" type="submit">Kod yuborish</button>
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
          email: form.email.value.trim(),
          password: form.password.value,
        });
        email = res.data.email;
        showToast("Tasdiqlash kodi emailingizga yuborildi", "success");
        renderVerify();
      } catch (err) {
        showToast(err.message);
      } finally {
        submitBtn.disabled = false;
      }
    });
  }

  function renderVerify() {
    document.getElementById("app").innerHTML = `
      <div class="auth-page">
        <form class="auth-card card" id="verify-form">
          <h1>Emailni tasdiqlang</h1>
          <p class="auth-card__switch">${escapeHtml(email)} manziliga 6 xonali kod yubordik.</p>
          <label>Tasdiqlash kodi
            <input type="text" name="code" class="input" inputmode="numeric" pattern="\\d{6}" maxlength="6" required autofocus />
          </label>
          <button class="btn btn--primary btn--block" type="submit">Tasdiqlash</button>
          <p class="auth-card__switch">
            Kod kelmadimi? <a href="#" id="resend-link">Qayta yuborish</a>
          </p>
        </form>
      </div>
    `;

    document.getElementById("verify-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const form = e.target;
      const submitBtn = form.querySelector("button[type=submit]");
      submitBtn.disabled = true;
      try {
        const res = await api.post("/auth/register/verify/", {
          email,
          code: form.code.value.trim(),
        });
        state.user = res.data;
        location.hash = "#/dashboard";
      } catch (err) {
        showToast(err.message);
      } finally {
        submitBtn.disabled = false;
      }
    });

    document.getElementById("resend-link").addEventListener("click", async (e) => {
      e.preventDefault();
      try {
        await api.post("/auth/register/resend/", { email });
        showToast("Kod qayta yuborildi", "success");
      } catch (err) {
        showToast(err.message);
      }
    });
  }

  renderForm();
};

window.pages.passwordReset = function renderPasswordReset() {
  let email = "";

  function renderRequest() {
    document.getElementById("app").innerHTML = `
      <div class="auth-page">
        <form class="auth-card card" id="reset-request-form">
          <h1>Parolni tiklash</h1>
          <label>Email
            <input type="email" name="email" class="input" placeholder="siz@example.com" required />
          </label>
          <button class="btn btn--primary btn--block" type="submit">Kod yuborish</button>
          <p class="auth-card__switch"><a href="#/login">Kirishga qaytish</a></p>
        </form>
      </div>
    `;

    document.getElementById("reset-request-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const form = e.target;
      const submitBtn = form.querySelector("button[type=submit]");
      submitBtn.disabled = true;
      try {
        email = form.email.value.trim();
        await api.post("/auth/password-reset/", { email });
        showToast("Agar bu email ro'yxatdan o'tgan bo'lsa, kod yuborildi", "success");
        renderConfirm();
      } catch (err) {
        showToast(err.message);
      } finally {
        submitBtn.disabled = false;
      }
    });
  }

  function renderConfirm() {
    document.getElementById("app").innerHTML = `
      <div class="auth-page">
        <form class="auth-card card" id="reset-confirm-form">
          <h1>Yangi parol</h1>
          <p class="auth-card__switch">${escapeHtml(email)} manziliga kod yubordik.</p>
          <label>Tasdiqlash kodi
            <input type="text" name="code" class="input" inputmode="numeric" pattern="\\d{6}" maxlength="6" required autofocus />
          </label>
          <label>Yangi parol
            <input type="password" name="new_password" class="input" required minlength="8" />
          </label>
          <button class="btn btn--primary btn--block" type="submit">Parolni yangilash</button>
        </form>
      </div>
    `;

    document.getElementById("reset-confirm-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const form = e.target;
      const submitBtn = form.querySelector("button[type=submit]");
      submitBtn.disabled = true;
      try {
        await api.post("/auth/password-reset/confirm/", {
          email,
          code: form.code.value.trim(),
          new_password: form.new_password.value,
        });
        showToast("Parol yangilandi. Endi kiring.", "success");
        location.hash = "#/login";
      } catch (err) {
        showToast(err.message);
      } finally {
        submitBtn.disabled = false;
      }
    });
  }

  renderRequest();
};
