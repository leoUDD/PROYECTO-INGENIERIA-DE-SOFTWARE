(function () {
  const KEY = "pitchTexto";

  document.addEventListener("DOMContentLoaded", () => {
    const box = document.getElementById("textoGuardado");
    if (!box) return;

    let texto = "";
    try {
      texto = sessionStorage.getItem(KEY) || "";
    } catch (_) {}

    if (texto.trim()) {
      box.textContent = texto;
    } else {
      box.innerHTML = '<p class="subtitle">No se encontró texto guardado. Vuelve a la etapa anterior y escribe tu pitch.</p>';
    }
  });

  const modal = document.getElementById("timeModal");
  const timerEl = document.getElementById("timer");
  const alarm = document.getElementById("alarmAudio");
  let ultimoSegundo = null;
  let alarmaDisparada = false;

  function abrirModal() {
    if (modal) modal.setAttribute("aria-hidden", "false");
  }

  function cerrarModal() {
    if (modal) modal.setAttribute("aria-hidden", "true");
  }

  document.getElementById("btnCerrarModal")?.addEventListener("click", cerrarModal);

  window.presentarPitchUI = {
    actualizarTimer(segundos) {
      if (!timerEl) return;

      const valor = Math.max(0, Number(segundos || 0));
      const min = String(Math.floor(valor / 60)).padStart(2, "0");
      const sec = String(valor % 60).padStart(2, "0");
      timerEl.textContent = `${min}:${sec}`;
      timerEl.dataset.seconds = valor;

      if (ultimoSegundo !== null && valor > 0) {
        alarmaDisparada = false;
      }

      if (valor === 0 && !alarmaDisparada && ultimoSegundo !== 0) {
        try {
          alarm && alarm.play();
        } catch (_) {}
        abrirModal();
        alarmaDisparada = true;
      }

      ultimoSegundo = valor;
    }
  };

  if (timerEl) {
    const inicial = Math.max(0, Number(timerEl.dataset.seconds || 90));
    window.presentarPitchUI.actualizarTimer(inicial);
  }
})();