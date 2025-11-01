(function () {
  const KEY = 'pitchTexto';

  // Mostrar el texto guardado
  document.addEventListener('DOMContentLoaded', () => {
    const box = document.getElementById('textoGuardado');
    if (!box) return;
    let texto = '';
    try { texto = sessionStorage.getItem(KEY) || ''; } catch (_) {}
    if (texto.trim()) {
      box.textContent = texto;
    } else {
      box.innerHTML = '<p class="subtitle">No se encontró texto guardado. Vuelve a la etapa anterior y escribe tu pitch.</p>';
    }
  });

  // Temporizador
  const timerEl = document.getElementById('timer');
  const btnStart = document.getElementById('btnStart');
  const btnPause = document.getElementById('btnPause');
  const btnReset = document.getElementById('btnReset');
  const alarm = document.getElementById('alarmAudio');

  let total = parseInt(timerEl?.dataset.seconds || '180', 10);
  let remaining = total;
  let intId = null;

  function fmt(sec) {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
  }
  function paint() { if (timerEl) timerEl.textContent = fmt(remaining); }

  function tick() {
    remaining -= 1;
    if (remaining <= 0) {
      clearInterval(intId); intId = null;
      remaining = 0; paint();
      try { alarm && alarm.play(); } catch(_) {}
      abrirModal();
      btnStart.disabled = false;
      btnPause.disabled = true;
      return;
    }
    paint();
  }

  function start() {
    if (intId) return;
    intId = setInterval(tick, 1000);
    btnStart.disabled = true;
    btnPause.disabled = false;
  }
  function pause() {
    clearInterval(intId);
    intId = null;
    btnStart.disabled = false;
    btnPause.disabled = true;
  }
  function reset() {
    pause();
    remaining = total;
    paint();
  }

  btnStart?.addEventListener('click', start);
  btnPause?.addEventListener('click', pause);
  btnReset?.addEventListener('click', reset);

  // Atajo Alt + Shift + S -> start/pause
  window.addEventListener('keydown', (e) => {
    if (e.altKey && e.shiftKey && (e.key.toLowerCase() === 's')) {
      if (intId) pause(); else start();
    }
  });

  // Modal
  const modal = document.getElementById('timeModal');
  function abrirModal(){ if (modal) modal.setAttribute('aria-hidden','false'); }
  function cerrarModal(){ if (modal) modal.setAttribute('aria-hidden','true'); }
  document.getElementById('btnCerrarModal')?.addEventListener('click', cerrarModal);

  // Copiar texto
  document.getElementById('btnCopiar')?.addEventListener('click', async () => {
    const txt = (document.getElementById('textoGuardado')?.textContent || '').trim();
    if (!txt) return;
    try {
      await navigator.clipboard.writeText(txt);
      alert('Texto copiado al portapapeles.');
    } catch {
      // Fallback
      const ta = document.createElement('textarea');
      ta.value = txt; document.body.appendChild(ta); ta.select();
      document.execCommand('copy'); document.body.removeChild(ta);
      alert('Texto copiado.');
    }
  });

  // Inicial
  paint();
})();
