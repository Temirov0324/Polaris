function openTripEditModal(trip, { onSaved } = {}) {
  const overlay = document.createElement("div");
  overlay.className = "modal-overlay";
  overlay.innerHTML = `
    <div class="modal">
      <h3>Maqsad summasini tahrirlash</h3>
      <form id="trip-edit-form">
        <label>Maqsad (USD)
          <input type="number" name="target_amount" class="input" min="0.01" step="0.01" value="${trip.target_amount ?? ""}" required />
        </label>
        <div class="modal__actions">
          <button type="button" class="btn btn--ghost" id="trip-edit-cancel">Bekor qilish</button>
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
  overlay.querySelector("#trip-edit-cancel").addEventListener("click", close);

  overlay.querySelector("#trip-edit-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const amount = Number(e.target.target_amount.value);
    if (!amount || amount <= 0) {
      showToast("Noto'g'ri summa");
      return;
    }
    try {
      await api.patch(`/trips/${trip.id}/`, { target_amount: amount });
      showToast("Maqsad yangilandi", "success");
      close();
      if (onSaved) onSaved();
    } catch (err) {
      showToast(err.message);
    }
  });
}

window.openTripEditModal = openTripEditModal;
