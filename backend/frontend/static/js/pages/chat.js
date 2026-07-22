window.pages = window.pages || {};

window.pages.chat = async function renderChat() {
  const app = document.getElementById("app");
  app.innerHTML = `
    <div class="page chat-page">
      <div class="chat-messages" id="chat-messages"><p class="loading">Yuklanmoqda&hellip;</p></div>
      <div class="chat-suggestions" id="chat-suggestions"></div>
      <form class="chat-input" id="chat-form">
        <input type="text" id="chat-text" class="input" placeholder="Savolingizni yozing..." maxlength="2000" required />
        <button type="submit" class="btn btn--primary">Yuborish</button>
      </form>
    </div>
  `;

  const messagesEl = document.getElementById("chat-messages");
  const suggestionsEl = document.getElementById("chat-suggestions");
  let history = [];

  try {
    const res = await api.get("/chat/messages/");
    history = res.data;
  } catch (err) {
    messagesEl.innerHTML = `<p class="error-text">Xatolik: ${escapeHtml(err.message)}</p>`;
    return;
  }

  renderMessages();

  if (history.length === 0) {
    messagesEl.innerHTML = `
      <div class="chat-bubble chat-bubble--assistant chat-bubble--welcome">
        Salom! Men PolarisAI yordamchisiman. Sizga quyidagilarda yordam bera olaman:
        <ul>
          <li>Sayohat byudjetini hisoblash</li>
          <li>Byudjetingizga mos yo'nalish tavsiya qilish</li>
          <li>Viza talablari haqida ma'lumot berish</li>
          <li>Sayohat rejasi yaratish va jamg'arish qo'shish — to'g'ridan-to'g'ri shu yerda, yozib ayting</li>
        </ul>
        Quyidagi tugmalardan birini bosing yoki savolingizni yozing.
      </div>
    `;
    const suggestions = ["$1000 bilan qayerga bora olaman?", "Turkiyaga qancha kerak?", "Vizasiz davlatlar qaysilar?"];
    suggestionsEl.innerHTML = suggestions.map((s) => `<button type="button" class="chip">${s}</button>`).join("");
    suggestionsEl.querySelectorAll(".chip").forEach((chip) => {
      chip.addEventListener("click", () => sendMessage(chip.textContent));
    });
  }

  document.getElementById("chat-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const input = document.getElementById("chat-text");
    const text = input.value.trim();
    if (!text) return;
    input.value = "";
    sendMessage(text);
  });

  function renderMessages() {
    messagesEl.innerHTML = history
      .map((m) => `<div class="chat-bubble chat-bubble--${m.role}">${escapeHtml(m.content)}</div>`)
      .join("");
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function renderTyping() {
    messagesEl.insertAdjacentHTML(
      "beforeend",
      '<div class="chat-bubble chat-bubble--assistant chat-bubble--typing" id="typing-indicator"><span></span><span></span><span></span></div>'
    );
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  async function sendMessage(text) {
    track("chat_message_sent");
    suggestionsEl.innerHTML = "";
    history.push({ role: "user", content: text });
    renderMessages();
    renderTyping();

    try {
      const res = await api.post("/chat/send/", { content: text });
      document.getElementById("typing-indicator")?.remove();
      history.push({ role: "assistant", content: res.data.message });
      renderMessages();
    } catch (err) {
      document.getElementById("typing-indicator")?.remove();
      showToast(err.message);
    }
  }
};
