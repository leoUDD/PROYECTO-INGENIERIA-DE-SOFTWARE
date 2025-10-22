// tematica.js
(function () {
  const cards = Array.from(document.querySelectorAll('.theme-card'));
  const cta = document.getElementById('btnContinuar');

  let selected = null;
  let selectedSlug = null;
  let selectedUrl = null;

  const norm = s => (s || '').toString().trim().toLowerCase();

  // ===== API global para los botones inline =====
  window.guardarTema = function (slug) {
    selectBySlug(slug);
  };

  // ===== CTA principal (botón inferior) =====
  if (cta) {
    cta.addEventListener('click', goToSelected);
  }

  // ===== Helpers =====
  function selectBySlug(slugRaw) {
    const slug = norm(slugRaw);
    const card = cards.find(c => norm(c.dataset.slug) === slug);
    if (!card) return;

    // Limpiar selección anterior
    cards.forEach(c => c.classList.remove('selected'));

    // Marcar card actual
    card.classList.add('selected');
    selected = card;
    selectedSlug = slug;

    const baseUrl = card.dataset.url || '/desafios/';
    selectedUrl = appendTema(baseUrl, slug);

    // Guardar selección en localStorage
    try {
      localStorage.setItem('temaSeleccionado', slug);
    } catch (_) {}

    if (cta) cta.disabled = false;
  }

  function appendTema(url, slug) {
    const sep = url.includes('?') ? '&' : '?';
    return `${url}${sep}tema=${encodeURIComponent(slug)}`;
  }

  function goToSelected() {
    if (!selectedUrl) return;
    window.location.href = selectedUrl;
  }
})();
