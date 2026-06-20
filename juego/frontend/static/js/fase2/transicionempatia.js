document.addEventListener("DOMContentLoaded", () => {
  function tJuego(clave, fallback = "") {
    const idioma = window.i18nJuego?.obtenerIdioma?.() || "es";
    return window.i18nJuego?.traducciones?.[idioma]?.[clave] || fallback;
  }

  function traducirBotonListoFase() {
    const botones = document.querySelectorAll(".next-step button, .btn-chip, .oai-btn-chip");

    botones.forEach((btn) => {
      if (!btn) return;

      const textoActual = (btn.textContent || "").trim().toLowerCase();

      if (
        btn.disabled ||
        textoActual.includes("esperando") ||
        textoActual.includes("waiting") ||
        textoActual.includes("listo") ||
        textoActual.includes("ready")
      ) {
        if (btn.disabled) {
          btn.textContent = tJuego("empatia_intro_boton_esperando", "Esperando...");
        } else {
          btn.textContent = tJuego("empatia_intro_boton_listo", "¡Estoy listo!");
        }
      }
    });
  }

  function traducirContadoresListos() {
    const textos = document.querySelectorAll(
      ".contador-fase, #contador-listos-fase, #texto-espera-fase, .oai-estado-listo"
    );

    textos.forEach((el) => {
      if (!el) return;

      const texto = el.textContent || "";
      const match = texto.match(/(\d+)\/(\d+)/);

      if (match) {
        el.textContent = `${match[1]}/${match[2]} ${tJuego("empatia_intro_grupos_listos", "grupos listos")}`;
      } else if (
        texto.toLowerCase().includes("esperando") ||
        texto.toLowerCase().includes("waiting")
      ) {
        el.textContent = tJuego("empatia_intro_esperando", "Esperando a los demás equipos...");
      }
    });
  }

  function traducirEmpatiaIntroDinamico() {
    traducirBotonListoFase();
    traducirContadoresListos();
  }

  setTimeout(traducirEmpatiaIntroDinamico, 300);

  window.addEventListener("idiomaJuegoCambiado", () => {
    traducirEmpatiaIntroDinamico();
  });
});