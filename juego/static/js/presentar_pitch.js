(function () {
  document.addEventListener("DOMContentLoaded", () => {
    const box = document.getElementById("textoGuardado");
    const timerEl = document.getElementById("timer");
    const alarm = document.getElementById("alarmAudio");
    let ultimoSegundo = null;
    let alarmaDisparada = false;

    function actualizarTextoPropio(texto) {
      if (!box) return;

      if (texto && texto.trim()) {
        box.textContent = texto;
      } else {
        box.innerHTML = '<p class="subtitle">No se encontró texto guardado. Vuelve a la etapa anterior y escribe tu pitch.</p>';
      }
    }

    function reproducirAlarmaSuave() {
      if (!alarm) return;
      try {
        alarm.currentTime = 0;
        alarm.play();
      } catch (_) {}
    }

    window.presentarPitchUI = {
      actualizarPitchPropio(texto) {
        actualizarTextoPropio(texto);
      },

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
          reproducirAlarmaSuave();
          alarmaDisparada = true;
        }

        ultimoSegundo = valor;
      }
    };

    if (timerEl) {
      const inicial = Math.max(0, Number(timerEl.dataset.seconds || 90));
      window.presentarPitchUI.actualizarTimer(inicial);
    }
  });
})();