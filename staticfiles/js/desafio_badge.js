(function () {
  const toggle = document.getElementById('dbToggle');
  const drawer = document.getElementById('dbDrawer');
  const closeBtn = document.getElementById('dbClose');

  const titleEl = document.getElementById('dbTitle');
  const shortEl = document.getElementById('dbShort');
  const descEl = document.getElementById('dbDesc');
  const ctaEl = document.querySelector('.db-chip-cta');

  const KEY = 'desafioSeleccionado';

  const stripLeadingEmoji = (s) =>
    (s || '').replace(/^\p{Extended_Pictographic}+\s*/u, '');

  let data = null;

  try {
    const raw = sessionStorage.getItem(KEY);
    data = raw ? JSON.parse(raw) : null;
  } catch (_) {
    data = null;
  }

  if (!data) {
    try {
      const raw2 = localStorage.getItem('desafioSeleccionadoData');
      const legacy = raw2 ? JSON.parse(raw2) : null;
      if (legacy) {
        data = {
          id: legacy.id,
          titulo: legacy.name,
          resumen: legacy.short || legacy.desc || '',
          url: '#',
          __descCompleta: legacy.desc || legacy.short || ''
        };
      }
    } catch (_) {}
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

  if (data) {
    const tituloLimpio = stripLeadingEmoji(data.titulo || 'Desafío seleccionado');

    if (titleEl) {
      titleEl.textContent = tituloLimpio;
    }

    const resumen = data.resumen || 'Desafío listo.';
    if (shortEl) {
      shortEl.textContent = resumen.length > 80
        ? resumen.slice(0, 80) + '…'
        : resumen;
    }

    const descCompleta = data.__descCompleta || data.resumen || '—';
    if (descEl) {
      descEl.textContent = descCompleta;
    }
  } else {
    if (titleEl) titleEl.textContent = 'Desafío no seleccionado';
    if (shortEl) shortEl.textContent = 'Elige un desafío para verlo aquí.';
    if (descEl) descEl.textContent = '—';
  }

  function openDrawer() {
    if (!drawer) return;
    drawer.hidden = false;
    toggle?.setAttribute('aria-expanded', 'true');
    if (ctaEl) ctaEl.textContent = '▲';
  }

  function closeDrawer() {
    if (!drawer) return;
    drawer.hidden = true;
    toggle?.setAttribute('aria-expanded', 'false');
    if (ctaEl) ctaEl.textContent = '▼';
  }

  toggle?.addEventListener('click', () => {
    if (!drawer) return;
    if (drawer.hidden) {
      openDrawer();
    } else {
      closeDrawer();
    }
  });

  closeBtn?.addEventListener('click', closeDrawer);
})();