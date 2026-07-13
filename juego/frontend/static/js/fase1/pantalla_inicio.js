document.addEventListener("DOMContentLoaded", () => {
  iniciarMusicaFondo();
  iniciarTypewriter();
  iniciarSincronizacionLobby();
});

function iniciarMusicaFondo() {
  const musicaFondo = document.getElementById("musica-fondo");

  if (!musicaFondo) return;

  musicaFondo.volume = 1;

  function intentarReproducir() {
    musicaFondo.play().catch(() => {
      const reanudar = () => {
        musicaFondo.play().catch(() => {});
        document.removeEventListener("click", reanudar);
        document.removeEventListener("touchstart", reanudar);
      };

      document.addEventListener("click", reanudar, { once: true });
      document.addEventListener("touchstart", reanudar, { once: true });
    });
  }

  intentarReproducir();
}

let sharedCtx = null;

function getCtx() {
  if (!sharedCtx || sharedCtx.state === "closed") {
    sharedCtx = new (window.AudioContext || window.webkitAudioContext)();
  }

  return sharedCtx;
}

function makeTypewriterSound() {
  try {
    const ctx = getCtx();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.type = "square";
    osc.frequency.value = 160 + Math.random() * 140;

    const t = ctx.currentTime;

    gain.gain.setValueAtTime(0.035, t);
    gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.05);

    osc.start(t);
    osc.stop(t + 0.05);
  } catch (e) {}
}

function typewrite(el, text, cb) {
  el.textContent = "";

  let i = 0;

  function tick() {
    if (i < text.length) {
      el.textContent += text[i++];
      makeTypewriterSound();
      setTimeout(tick, 32 + Math.random() * 28);
    } else {
      setTimeout(cb, 150);
    }
  }

  tick();
}

function tJuego(clave, fallback = "") {
  const idioma = window.i18nJuego?.obtenerIdioma?.() || "es";
  return window.i18nJuego?.traducciones?.[idioma]?.[clave] || fallback;
}

function actualizarTextosTypewriter() {
  document.querySelectorAll("[data-i18n-text]").forEach((el) => {
    const clave = el.getAttribute("data-i18n-text");
    const fallback = el.getAttribute("data-text") || "";
    el.setAttribute("data-text", tJuego(clave, fallback));
  });
}

function typewriteSequence(elements) {
  actualizarTextosTypewriter();

  let i = 0;

  function next() {
    if (i >= elements.length) return;

    const el = elements[i++];
    const text = el.getAttribute("data-text") || "";

    typewrite(el, text, next);
  }

  setTimeout(next, 500);
}

function iniciarTypewriter() {
  const elementos = [...document.querySelectorAll("[data-text]")];
  typewriteSequence(elementos);
}

function iniciarSincronizacionLobby() {
  const boton = document.getElementById("btnComenzar");
  const estado = document.getElementById("estado-listo-lobby");

  const sesionId = document.body.dataset.sesionId;
  const grupoId = document.body.dataset.grupoId;
  const csrfToken = document.body.dataset.csrfToken;

  if (!boton || !estado || !sesionId || !grupoId) return;

  async function refrescarEstado() {
    try {
      const res = await fetch(`/sesion/${sesionId}/estado/`);
      const data = await res.json();

      const listos = data.gruposListosLobby || 0;
      const total = data.totalGrupos || 0;

      estado.textContent = `${listos}/${total} ${tJuego("bienvenida_grupos_listos", "grupos listos")}`;

      const miGrupo = (data.grupos || []).find((g) => Number(g.id) === Number(grupoId));

      if (miGrupo && miGrupo.listoLobby) {
        boton.disabled = true;
        boton.textContent = tJuego("bienvenida_boton_listo_ok", "¡Listo!");
      }

      if (data.faseActual !== "f1_bienvenida" && data.rutaAlumno) {
        window.location.href = data.rutaAlumno;
      }
    } catch (e) {
      console.error(e);
    }
  }

  boton.addEventListener("click", async () => {
    boton.disabled = true;

    try {
      const res = await fetch(`/grupo/${grupoId}/listo/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({ fase: "lobby" }),
      });

      const data = await res.json();

      if (data.ok) {
        estado.textContent = `${data.gruposListos}/${data.totalGrupos} ${tJuego("bienvenida_grupos_listos", "grupos listos")}`;
        boton.textContent = tJuego("bienvenida_boton_listo_ok", "¡Listo!");

        if (data.faseActual !== "f1_bienvenida" && data.rutaAlumno) {
          window.location.href = data.rutaAlumno;
          return;
        }
      } else {
        boton.disabled = false;
        boton.textContent = tJuego("bienvenida_boton_listo", "¡Estoy listo!");
      }
    } catch (e) {
      boton.disabled = false;
      boton.textContent = tJuego("bienvenida_boton_listo", "¡Estoy listo!");
      console.error(e);
    }
  });

  setInterval(refrescarEstado, 2000);
  refrescarEstado();
}