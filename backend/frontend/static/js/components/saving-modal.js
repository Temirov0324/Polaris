function openSavingModal(tripId, { date, onSaved } = {}) {
  const entryDate = date || todayIso();

  const overlay = document.createElement("div");
  overlay.className = "modal-overlay";
  overlay.innerHTML = `
    <div class="modal">
      <h3>Bugun qancha jamg'ardingiz?</h3>
      <div class="modal__presets">
        <button type="button" class="btn btn--chip" data-amount="5">$5</button>
        <button type="button" class="btn btn--chip" data-amount="10">$10</button>
        <button type="button" class="btn btn--chip" data-amount="20">$20</button>
        <button type="button" class="btn btn--chip" data-amount="other">Boshqa</button>
      </div>
      <form id="saving-modal-form" class="modal__form" hidden>
        <label>Summa (USD)
          <input type="number" name="amount" class="input" min="0.01" step="0.01" required />
        </label>
        <label>Izoh (ixtiyoriy)
          <input type="text" name="note" class="input" maxlength="200" />
        </label>
        <div class="modal__actions">
          <button type="button" class="btn btn--ghost" id="modal-cancel">Bekor qilish</button>
          <button type="submit" class="btn btn--primary">Saqlash</button>
        </div>
      </form>
    </div>
  `;
  document.body.appendChild(overlay);

  const close = () => overlay.remove();
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) close();
  });

  const form = overlay.querySelector("#saving-modal-form");

  async function submitAmount(amount, note) {
    if (!amount || amount <= 0) {
      showToast("Noto'g'ri summa");
      return;
    }
    try {
      await api.post(`/trips/${tripId}/savings/`, { amount, date: entryDate, note: note || "" });
      track("saving_entry_added", { amount });
      showToast("Saqlandi!", "success");
      close();
      if (onSaved) onSaved();
    } catch (err) {
      showToast(err.message);
    }
  }

  overlay.querySelectorAll(".modal__presets .btn--chip").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (btn.dataset.amount === "other") {
        form.hidden = false;
        form.amount.focus();
        return;
      }
      submitAmount(Number(btn.dataset.amount), "");
    });
  });

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    submitAmount(Number(form.amount.value), form.note.value.trim());
  });

  overlay.querySelector("#modal-cancel").addEventListener("click", close);
}

window.openSavingModal = openSavingModal;
