(function(){
  const toggle = document.getElementById('dbToggle');
  const drawer = document.getElementById('dbDrawer');
  const closeBtn = document.getElementById('dbClose');

  const titleEl = document.getElementById('dbTitle');
  const shortEl = document.getElementById('dbShort');
  const descEl  = document.getElementById('dbDesc');

  const KEY = 'desafioSeleccionado';

  // Quita emojis y espacios iniciales si vinieron pegados en el título
  const stripLeadingEmoji = (s) =>
    (s || '').replace(/^\p{Extended_Pictographic}+\s*/u, '');

  // 1) Lee el formato actual (sessionStorage)
  let data = null;
  try {
    const raw = sessionStorage.getItem(KEY);
    data = raw ? JSON.parse(raw) : null;
  } catch (_) { data = null; }

  // 2) Fallbacks (formatos antiguos)
  if (!data) {
    try {
      const raw2 = localStorage.getItem('desafioSeleccionadoData');
      const legacy = raw2 ? JSON.parse(raw2) : null; // { id, name, short, desc }
      if (legacy) {
        data = {
          id: legacy.id,
          titulo: legacy.name,
          resumen: legacy.short || legacy.desc || '',
          url: '#',
          __descCompleta: legacy.desc || legacy.short || ''
        };
      }
    } catch(_) {}
  }
  if (!data) {
    const legacyId = localStorage.getItem('desafioSeleccionado');
    if (legacyId) {
      data = {
        id: legacyId,
        titulo: 'Desafío #' + legacyId,
        resumen: 'Desafío seleccionado.',
        url: '#'
      };
    }
  }

  // 3) Pintado sin emoji
  if (data) {
    const tituloLimpio = stripLeadingEmoji(data.titulo || 'Desafío seleccionado');
    titleEl.textContent = tituloLimpio;               // ← sin emoji
    const resumen = data.resumen || 'Desafío listo.';
    shortEl.textContent = resumen.length > 80 ? resumen.slice(0, 80) + '…' : resumen;

    const descCompleta = data.__descCompleta || data.resumen || '—';
    descEl.textContent = descCompleta;
  } else {
    titleEl.textContent = 'Desafío no seleccionado';
    shortEl.textContent = 'Elige un desafío para verlo aquí.';
    descEl.textContent  = '—';
  }

  // 4) Toggle del drawer
  function openDrawer(){
    drawer.hidden = false;
    toggle?.setAttribute('aria-expanded', 'true');
  }
  function closeDrawer(){
    drawer.hidden = true;
    toggle?.setAttribute('aria-expanded', 'false');
  }
  toggle?.addEventListener('click', () => {
    if (!drawer) return;
    if (drawer.hidden) { openDrawer(); } else { closeDrawer(); }
  });
  closeBtn?.addEventListener('click', closeDrawer);
})();
