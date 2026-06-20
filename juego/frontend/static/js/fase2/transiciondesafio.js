document.addEventListener("DOMContentLoaded", () => {
  inicializarTraduccionesDesafios();
  inicializarMusicaDesafios();
});

function inicializarTraduccionesDesafios() {
  function tJuego(clave, fallback = "") {
    const idioma = window.i18nJuego?.obtenerIdioma?.() || "es";
    return window.i18nJuego?.traducciones?.[idioma]?.[clave] || fallback;
  }

  function traducirBotonListoFase() {
    const botones = document.querySelectorAll(".next-step button, .btn-chip");

    botones.forEach((btn) => {
      if (!btn) return;

      const textoActual = (btn.textContent || "").trim().toLowerCase();

      if (btn.disabled || textoActual.includes("esperando") || textoActual.includes("waiting")) {
        btn.textContent = tJuego("desafios_intro_boton_esperando", "Esperando...");
      } else {
        btn.textContent = tJuego("desafios_intro_boton_listo", "¡Estoy listo!");
      }
    });
  }

  function traducirContadoresListos() {
    const textos = document.querySelectorAll(".contador-fase, #contador-listos-fase, #texto-espera-fase");

    textos.forEach((el) => {
      if (!el) return;

      const texto = el.textContent || "";
      const match = texto.match(/(\d+)\/(\d+)/);

      if (match) {
        el.textContent = `${match[1]}/${match[2]} ${tJuego("desafios_intro_grupos_listos", "grupos listos")}`;
      } else if (texto.toLowerCase().includes("esperando") || texto.toLowerCase().includes("waiting")) {
        el.textContent = tJuego("desafios_intro_esperando", "Esperando a los demás equipos...");
      }
    });
  }

  function traducirDesafiosIntroDinamico() {
    traducirBotonListoFase();
    traducirContadoresListos();
  }

  setTimeout(traducirDesafiosIntroDinamico, 300);

  window.addEventListener("idiomaJuegoCambiado", () => {
    traducirDesafiosIntroDinamico();
  });
}

function inicializarMusicaDesafios() {
  const audio = document.getElementById("musica-desafios");
  const btn = document.getElementById("btn-musica-desafios");

  if (!audio || !btn) return;

  audio.volume = 0.4;

  function arrancarMusica() {
    audio.play().catch(() => {});
    document.removeEventListener("click", arrancarMusica);
    document.removeEventListener("touchstart", arrancarMusica);
  }

  function alternarMusica() {
    audio.muted = !audio.muted;
    btn.textContent = audio.muted ? "🔇" : "🔊";
    btn.title = audio.muted ? "Activar música" : "Silenciar música";
    btn.setAttribute("aria-label", audio.muted ? "Activar música" : "Silenciar música");
  }

  document.addEventListener("click", arrancarMusica);
  document.addEventListener("touchstart", arrancarMusica);

  btn.addEventListener("click", alternarMusica);

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      audio.pause();
    } else if (!audio.muted) {
      audio.play().catch(() => {});
    }
  });

  window.addEventListener("beforeunload", () => {
    audio.pause();
  });
}