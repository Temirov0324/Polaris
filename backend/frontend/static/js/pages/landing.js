window.pages = window.pages || {};

window.pages.landing = function renderLanding() {
  document.getElementById("app").innerHTML = `
    <div class="landing">
      <section class="landing__hero">
        <div class="landing__blob landing__blob--a"></div>
        <div class="landing__blob landing__blob--b"></div>
        <span class="landing__eyebrow">✈️ PolarisAI</span>
        <h1>Sayohat orzu emas, reja</h1>
        <p>PolarisAI — sayohat byudjetingizni hisoblaydi va jamg'arish rejangizni tuzadi.</p>
        <div class="landing__cta">
          <a class="btn btn--primary btn--large" href="#/register">Boshlash</a>
          <a class="btn btn--ghost btn--large" href="#/login">Kirish</a>
        </div>
      </section>
      <section class="landing__features">
        <div class="feature-card">
          <span class="feature-card__icon">🧮</span>
          <h3>Qancha kerakligini biz hisoblaymiz</h3>
          <p>Yo'nalish, sana va uslubga qarab real narxlar asosida byudjet diapazonini ko'rasiz.</p>
        </div>
        <div class="feature-card">
          <span class="feature-card__icon">🔥</span>
          <h3>Kuniga bir oz — va siz yo'ldasiz</h3>
          <p>Kunlik jamg'arish maqsadini kuzating, streak saqlang, sayohat sanasiga tayyor bo'ling.</p>
        </div>
        <div class="feature-card">
          <span class="feature-card__icon">💬</span>
          <h3>AI yordamchi</h3>
          <p>Byudjet, yo'nalish va viza savollariga darhol javob oling.</p>
        </div>
      </section>
    </div>
  `;
};
