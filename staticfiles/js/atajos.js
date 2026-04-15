// static/js/atajos.js
(function () {
  'use strict';

  function clearAllTimers() {
    try {
      let id = window.setTimeout(() => {}, 0);
      while (id--) clearTimeout(id);
      id = window.setInterval(() => {}, 0);
      while (id--) clearInterval(id);
    } catch (_) {}
  }

  function goto(url) {
    if (!url) return;
    clearAllTimers();
    window.location.assign(url);
  }

  function currentPath() {
    return window.location.pathname.replace(/\/+$/, '') || '/';
  }

  function getFlow() {
    const raw = Array.isArray(window.FLUJO_JUEGO) ? window.FLUJO_JUEGO : [];
    return raw.map(u => {
      try {
        const url = new URL(u, window.location.origin);
        return url.pathname.replace(/\/+$/, '') || '/';
      } catch { return (u || '').replace(/\/+$/, '') || '/'; }
    }).filter(Boolean);
  }

  function navNext() {
    const flow = getFlow();
    if (!flow.length) return;
    const p = currentPath();
    let i = flow.indexOf(p);
    if (i < 0) i = 0;
    const next = flow[(i + 1) % flow.length];
    goto(next);
  }

  function navPrev() {
    const flow = getFlow();
    if (!flow.length) return;
    const p = currentPath();
    let i = flow.indexOf(p);
    if (i < 0) i = 0;
    const prev = flow[(i - 1 + flow.length) % flow.length];
    goto(prev);
  }

  function onKey(e) {
    const el = document.activeElement;
    if (el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.isContentEditable)) return;

    const isRight = e.key === 'ArrowRight';
    const isLeft  = e.key === 'ArrowLeft';

    // PRIMARIO (fiable): Ctrl + Alt + Flechas
    if (e.ctrlKey && e.altKey && (isRight || isLeft)) {
      e.preventDefault();
      e.stopPropagation();
      if (isRight) navNext(); else navPrev();
      return;
    }

    // OPCIONAL (si el navegador lo permite): Alt + Flechas
    if (e.altKey && !e.ctrlKey && !e.metaKey && (isRight || isLeft)) {
      // En muchos navegadores el Alt+Flecha es de historial; a veces no llega aquí.
      e.preventDefault();
      e.stopPropagation();
      if (isRight) navNext(); else navPrev();
    }
  }

  window.addEventListener('keydown', onKey, { capture: true });
})();
