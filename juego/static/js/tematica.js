// tematica.js — selección SOLO con el botón "Elegir"
(function () {
  const cards = Array.from(document.querySelectorAll('.theme-card'));
  const cta = document.getElementById('btnContinuar');

  // Estado inicial limpio (sin preseleccionar nada)
  try { localStorage.removeItem('temaSeleccionado'); } catch (_) {}
  if (cta) cta.disabled = true;

  // API global para los botones inline del HTML: onclick="guardarTema('salud')"
  window.guardarTema = function (slugRaw) {
    const slug = norm(slugRaw);
    selectBySlug(slug);
  };

  // Helpers
  function norm(s) { return (s || '').toString().trim().toLowerCase(); }

  function selectBySlug(slug) {
    // Busca la card por data-slug
    const card = cards.find(c => norm(c.dataset.slug) === slug);
    if (!card) return;

    // Quita selección previa
    cards.forEach(c => c.classList.remove('selected'));

    // Marca selección visual
    card.classList.add('selected');

    // Guarda selección
    try { localStorage.setItem('temaSeleccionado', slug); } catch (_) {}

    // Habilita CTA
    if (cta) cta.disabled = false;

    // Opcional: feedback en los botones "Elegir"
    updateSelectButtons(card);
  }

  function updateSelectButtons(selectedCard) {
    const allButtons = document.querySelectorAll('.theme-card .btn.select');
    allButtons.forEach(btn => {
      btn.textContent = 'Elegir';
      btn.disabled = false;
    });
    const btn = selectedCard.querySelector('.btn.select');
    if (btn) {
      btn.textContent = 'Seleccionado ✅';
      btn.disabled = true;
    }
  }

  // Sincroniza si se cambiara en otra pestaña
  window.addEventListener('storage', () => {
    const saved = localStorage.getItem('temaSeleccionado');
    if (!saved) {
      // Si alguien borró la selección desde otra pestaña
      cards.forEach(c => c.classList.remove('selected'));
      if (cta) cta.disabled = true;
      const allButtons = document.querySelectorAll('.theme-card .btn.select');
      allButtons.forEach(b => { b.textContent = 'Elegir'; b.disabled = false; });
    }
  });
})();
