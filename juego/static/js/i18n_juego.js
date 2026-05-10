/* ============================================================
   Misión Emprende UDD — i18n_juego.js
   Traducción ES / EN con localStorage
   ============================================================ */

(function () {
  const STORAGE_KEY = "idiomaJuego";

  const traducciones = {
    es: {
    mapa_topbar: "Habilidades de misión",
mapa_clasificado: "Clasificado",
mapa_selecciona_punto: "Selecciona el punto en el mapa",
mapa_hint: "Selecciona la habilidad activa y continúa la misión",

mapa_trabajo_nombre: "Trabajo en equipo",
mapa_trabajo_sub: "Colaboración",
mapa_trabajo_desc: "Escucha, comparte y avancen como uno solo. Un equipo sincronizado es el arma más poderosa de la misión.",

mapa_empatia_nombre: "Empatía",
mapa_empatia_sub: "Comprensión",
mapa_empatia_desc: "Antes de actuar, entiende qué siente, qué necesita y qué espera la persona que buscas ayudar.",

mapa_creatividad_nombre: "Creatividad",
mapa_creatividad_sub: "Innovación",
mapa_creatividad_desc: "Las soluciones obvias no bastan. Piensa diferente, combina lo inesperado y sorprende al mundo.",

mapa_final_nombre: "Misión final",
mapa_final_sub: "Comunicación + Negociación",
mapa_final_desc: "Comunica tu propuesta con claridad, presenta tu solución y usa la retroalimentación para mejorar.",

mapa_boton_trabajo: "Continuar a trabajo en equipo",
mapa_boton_empatia: "Continuar a empatía",
mapa_boton_creatividad: "Continuar a creatividad",
mapa_boton_final: "Continuar a misión final",
mapa_hint_confirmada: "// HABILIDAD CONFIRMADA — CONTINÚA LA MISIÓN",
mapa_habilidad_completada: "HABILIDAD COMPLETADA ✓",
mapa_bloqueado: "BLOQUEADO",
mapa_cargando: "CARGANDO MISIÓN...",
      idioma_es: "Español",
      idioma_en: "English",

      hud_ranking: "🏆 Ranking",
      hud_escuadron: "Escuadrón",

      pitch_titulo: "Pitch del equipo",
      pitch_subtitulo: "Presenten su solución usando el texto que prepararon.",
      pitch_presentacion_actual: "Presentación actual",
      pitch_temporizador: "Temporizador",
      pitch_iniciar_presentacion: "⚡ Iniciar presentación",
      pitch_solo_equipo_actual: "Solo el equipo que está presentando puede iniciar el temporizador.",
      pitch_mi_equipo: "Pitch de mi equipo",
      pitch_orden: "Orden del pitch",
      pitch_esperando_sorteo: "Esperando sorteo...",
      pitch_sin_texto: "No se encontró texto guardado. Vuelve a la etapa anterior y escribe tu pitch.",
      pitch_sin_foto: "Este equipo no subió foto de su solución LEGO.",
      pitch_consejo: "Consejo: enfoquen problema, solución, impacto y próximos pasos.",

      mapa_titulo: "Habilidades de misión",
      mapa_selecciona: "Selecciona el punto en el mapa",
      mapa_mision_final: "Misión final",
      mapa_continuar_final: "Continuar a misión final",

      boton_continuar: "Continuar",
      boton_entendido: "Entendido",
      boton_ok: "OK",
      boton_esperando: "Esperando...",
    },

    en: {
      idioma_es: "Español",
      idioma_en: "English",
      mapa_topbar: "Mission skills",
mapa_clasificado: "Classified",
mapa_selecciona_punto: "Select a point on the map",
mapa_hint: "Select the active skill and continue the mission",

mapa_trabajo_nombre: "Teamwork",
mapa_trabajo_sub: "Collaboration",
mapa_trabajo_desc: "Listen, share, and move forward as one. A synchronized team is the mission’s strongest weapon.",

mapa_empatia_nombre: "Empathy",
mapa_empatia_sub: "Understanding",
mapa_empatia_desc: "Before acting, understand what the person feels, needs, and expects.",

mapa_creatividad_nombre: "Creativity",
mapa_creatividad_sub: "Innovation",
mapa_creatividad_desc: "Obvious solutions are not enough. Think differently, combine the unexpected, and surprise the world.",

mapa_final_nombre: "Final mission",
mapa_final_sub: "Communication + Negotiation",
mapa_final_desc: "Communicate your proposal clearly, present your solution, and use feedback to improve.",

mapa_boton_trabajo: "Continue to teamwork",
mapa_boton_empatia: "Continue to empathy",
mapa_boton_creatividad: "Continue to creativity",
mapa_boton_final: "Continue to final mission",
mapa_hint_confirmada: "// SKILL CONFIRMED — CONTINUE THE MISSION",
mapa_habilidad_completada: "SKILL COMPLETED ✓",
mapa_bloqueado: "LOCKED",
mapa_cargando: "LOADING MISSION...",
      hud_ranking: "🏆 Ranking",
      hud_escuadron: "Squad",

      pitch_titulo: "Team Pitch",
      pitch_subtitulo: "Present your solution using the text you prepared.",
      pitch_presentacion_actual: "Current presentation",
      pitch_temporizador: "Timer",
      pitch_iniciar_presentacion: "⚡ Start presentation",
      pitch_solo_equipo_actual: "Only the team currently presenting can start the timer.",
      pitch_mi_equipo: "My team’s pitch",
      pitch_orden: "Pitch order",
      pitch_esperando_sorteo: "Waiting for draw...",
      pitch_sin_texto: "No saved text was found. Go back to the previous stage and write your pitch.",
      pitch_sin_foto: "This team did not upload a photo of their LEGO solution.",
      pitch_consejo: "Tip: focus on the problem, solution, impact, and next steps.",

      mapa_titulo: "Mission skills",
      mapa_selecciona: "Select a point on the map",
      mapa_mision_final: "Final mission",
      mapa_continuar_final: "Continue to final mission",

      boton_continuar: "Continue",
      boton_entendido: "Got it",
      boton_ok: "OK",
      boton_esperando: "Waiting...",
    }
  };

  function obtenerIdioma() {
    return localStorage.getItem(STORAGE_KEY) || "es";
  }

  function guardarIdioma(idioma) {
    localStorage.setItem(STORAGE_KEY, idioma);
  }

  function traducirElemento(el, idioma) {
    const clave = el.dataset.i18n;
    const texto = traducciones[idioma]?.[clave];

    if (!clave || texto === undefined) return;

    if (el.dataset.i18nAttr === "placeholder") {
      el.setAttribute("placeholder", texto);
      return;
    }

    if (el.dataset.i18nAttr === "title") {
      el.setAttribute("title", texto);
      return;
    }

    if (el.dataset.i18nHtml === "true") {
      el.innerHTML = texto;
      return;
    }

    el.textContent = texto;
  }

  function aplicarTraduccion(idioma = obtenerIdioma()) {
    document.documentElement.lang = idioma;

    document.querySelectorAll("[data-i18n]").forEach(el => {
      traducirElemento(el, idioma);
    });

    document.querySelectorAll("[data-i18n-value]").forEach(el => {
      const clave = el.dataset.i18nValue;
      const texto = traducciones[idioma]?.[clave];

      if (texto !== undefined) {
        el.value = texto;
      }
    });

    const selector = document.getElementById("selectorIdiomaJuego");
    if (selector) {
      selector.value = idioma;
    }
  }

  function crearSelectorIdioma() {
  let box = document.getElementById("idiomaJuegoBox");

  if (!box) {
    box = document.createElement("div");
    box.id = "idiomaJuegoBox";
    box.className = "idioma-juego-box";

    box.innerHTML = `
      <span class="idioma-juego-icon">🌐</span>
      <select id="selectorIdiomaJuego" class="idioma-juego-select" aria-label="Idioma del juego">
        <option value="es">ES</option>
        <option value="en">EN</option>
      </select>
    `;

    document.body.appendChild(box);
  }

  const selector = document.getElementById("selectorIdiomaJuego");
  if (!selector) return;

  selector.value = obtenerIdioma();

  if (selector.dataset.listenerIdioma === "true") return;

  selector.dataset.listenerIdioma = "true";

  selector.addEventListener("change", () => {
    guardarIdioma(selector.value);
    aplicarTraduccion(selector.value);

    window.dispatchEvent(new CustomEvent("idiomaJuegoCambiado", {
      detail: { idioma: selector.value }
    }));
  });
}

  document.addEventListener("DOMContentLoaded", () => {
    crearSelectorIdioma();
    aplicarTraduccion();


  });

  window.i18nJuego = {
    traducir: aplicarTraduccion,
    obtenerIdioma,
    guardarIdioma,
    traducciones
  };
})();