(function () {
  const KEY = 'pitchTexto';
  const textarea = document.getElementById('pitch-text');
  const btnPresentar = document.getElementById('btnPresentar');
  const btnLimpiar = document.getElementById('btnLimpiar');

  // Cargar si existía algo guardado
  try {
    const prev = sessionStorage.getItem(KEY);
    if (prev) textarea.value = prev;
  } catch (_) {}

  // Guardado en vivo
  let saveTimer;
  textarea.addEventListener('input', () => {
    try { sessionStorage.setItem(KEY, textarea.value); } catch (_) {}
    // hint sutil
    const hint = document.getElementById('saveHint');
    if (hint) {
      hint.textContent = 'Guardado…';
      clearTimeout(saveTimer);
      saveTimer = setTimeout(() => hint.textContent = 'Los cambios se guardan automáticamente.', 800);
    }
  });

  btnLimpiar.addEventListener('click', () => {
    textarea.value = '';
    try { sessionStorage.removeItem(KEY); } catch (_) {}
    const hint = document.getElementById('saveHint');
    if (hint) hint.textContent = 'Contenido borrado.';
  });

  btnPresentar.addEventListener('click', () => {
    window.location.href = PRESENTAR_URL;
  });

  // Inyecta la URL de destino desde el template sin mezclar lógica
  // En templates, justo antes de incluir este archivo, puedes definir:
  // <script>const PRESENTAR_URL = "{% url 'presentar_pitch' %}";</script>
})();
