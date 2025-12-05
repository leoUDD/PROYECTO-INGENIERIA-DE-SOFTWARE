// tematica.js — selección SOLO con el botón "Elegir"
(function () {
  const cards = Array.from(document.querySelectorAll('.theme-card'));
  const cta = document.getElementById('btnContinuar');

  // Estado inicial limpio (sin preseleccionar nada)
  try { localStorage.removeItem('temaSeleccionado'); } catch (_) {}
  if (cta) cta.disabled = true;

  window.guardarTema = function (slugRaw) {
    const slug = norm(slugRaw);
    selectBySlug(slug);
  };

  function norm(s) { return (s || '').toString().trim().toLowerCase(); }

  function selectBySlug(slug) {
    const card = cards.find(c => norm(c.dataset.slug) === slug);
    if (!card) return;
    cards.forEach(c => c.classList.remove('selected'));
    card.classList.add('selected');
    try { localStorage.setItem('temaSeleccionado', slug); } catch (_) {}
    if (cta) cta.disabled = false;
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

  window.addEventListener('storage', () => {
    const saved = localStorage.getItem('temaSeleccionado');
    if (!saved) {
      cards.forEach(c => c.classList.remove('selected'));
      if (cta) cta.disabled = true;
      const allButtons = document.querySelectorAll('.theme-card .btn.select');
      allButtons.forEach(b => { b.textContent = 'Elegir'; b.disabled = false; });
    }
  });
})();
