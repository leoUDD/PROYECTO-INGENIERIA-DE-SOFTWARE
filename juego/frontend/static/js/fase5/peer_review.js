document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("peerReviewForm");
    const btn = document.getElementById("btnEnviarEvaluacion");
    const pageData = document.body.dataset;
    const sesionId = pageData.sesionId || "";
    const grupoObjetivoInicial = pageData.grupoObjetivoId || "";
    const timerEvaluacion = document.getElementById("timerEvaluacion");

    let redirigiendo = false;
    let fallbackInicioEvaluacion = Date.now();
    const FALLBACK_SEGUNDOS_EVALUACION = 90;

    function tPeer(clave, fallback) {
      try {
        const idioma = window.i18nJuego?.obtenerIdioma?.() || "es";
        return window.i18nJuego?.traducciones?.[idioma]?.[clave] || fallback;
      } catch (e) {
        return fallback;
      }
    }

    function aplicarTextosPeer() {
      document.title = tPeer("peer_document_title", "Misión Emprende UDD — Evaluación de Proyectos");

      const comment = document.getElementById("comment");
      if (comment) {
        comment.placeholder = tPeer(
          "peer_comentario_placeholder",
          "Puedes escribir una fortaleza o una sugerencia concreta para el equipo..."
        );
      }

      document.querySelectorAll("[data-criterio-key]").forEach(label => {
        const key = label.dataset.criterioKey;
        const fallback = label.textContent.trim();
        label.textContent = tPeer(`peer_criterio_${key}`, fallback);
      });
    }

    function formatearTiempo(segundos) {
      segundos = Math.max(Number(segundos || 0), 0);
      const min = Math.floor(segundos / 60);
      const seg = segundos % 60;
      return `${min}:${String(seg).padStart(2, "0")}`;
    }

    function segundosFallback() {
      const transcurridos = Math.floor((Date.now() - fallbackInicioEvaluacion) / 1000);
      return Math.max(FALLBACK_SEGUNDOS_EVALUACION - transcurridos, 0);
    }

    function segundosParaMostrar(data) {
      const segundosBackend = Number(data?.segundosRestantes || 0);

      if (segundosBackend > 0) {
        return segundosBackend;
      }

      if (data?.faseActual === "f5_evaluacion_pitch") {
        return segundosFallback();
      }

      return 0;
    }

    function textoScore(valor) {
      const v = Number(valor);

      if (v <= 1) {
        return {
          emoji: "😕",
          texto: "1 / 5"
        };
      }

      if (v === 2) {
        return {
          emoji: "🙂",
          texto: "2 / 5"
        };
      }

      if (v === 3) {
        return {
          emoji: "😊",
          texto: "3 / 5"
        };
      }

      if (v === 4) {
        return {
          emoji: "🤩",
          texto: "4 / 5"
        };
      }

      return {
        emoji: "🚀",
        texto: "5 / 5"
      };
    }

    function actualizarSlider(slider) {
      const key = slider.dataset.key;
      const valor = Number(slider.value || 3);
      const resultado = textoScore(valor);

      const emoji = document.getElementById(`score_emoji_${key}`);
      const text = document.getElementById(`score_text_${key}`);
      const pill = document.getElementById(`score_pill_${key}`);

      if (emoji) emoji.textContent = resultado.emoji;
      if (text) text.textContent = resultado.texto;

      const porcentaje = ((valor - 1) / 4) * 100;

      slider.style.background =
        `linear-gradient(to right, #00C8FF 0%, #00C8FF ${porcentaje}%, #334155 ${porcentaje}%, #334155 100%)`;

      if (pill) {
        pill.style.transform = `scale(${1 + (valor - 3) * 0.025})`;

        if (valor <= 2) {
          pill.style.boxShadow = "0 0 14px rgba(248, 113, 113, 0.35)";
          pill.style.borderColor = "rgba(248, 113, 113, 0.75)";
        } else if (valor === 3) {
          pill.style.boxShadow = "0 0 14px rgba(0, 200, 255, 0.25)";
          pill.style.borderColor = "rgba(0, 200, 255, 0.78)";
        } else {
          pill.style.boxShadow = "0 0 18px rgba(34, 197, 94, 0.42)";
          pill.style.borderColor = "rgba(34, 197, 94, 0.78)";
        }
      }
    }

    aplicarTextosPeer();

    document.querySelectorAll(".score-range").forEach(slider => {
      actualizarSlider(slider);
      slider.addEventListener("input", () => actualizarSlider(slider));
      slider.addEventListener("change", () => actualizarSlider(slider));
    });

    if (form && btn) {
      form.addEventListener("submit", () => {
        btn.disabled = true;
        btn.textContent = tPeer("peer_boton_enviando", "Enviando...");
      });
    }

    async function revisarEstadoEvaluacion() {
      if (redirigiendo) return;

      try {
        const res = await fetch(`/sesion/${sesionId}/estado/`, {
          credentials: "same-origin",
          cache: "no-store"
        });

        if (!res.ok) return;

        const data = await res.json();

        if (timerEvaluacion) {
          timerEvaluacion.textContent = formatearTiempo(segundosParaMostrar(data));
        }

        if (data.faseActual !== "f5_evaluacion_pitch") {
          if (data.rutaAlumno) {
            redirigiendo = true;
            window.location.replace(data.rutaAlumno);
          }
          return;
        }

        const grupoActual = data.grupoActual;

        if (!grupoActual || String(grupoActual.id) !== String(grupoObjetivoInicial)) {
          redirigiendo = true;
          window.location.reload();
        }
      } catch (error) {
        console.error("Error sincronizando evaluación:", error);
      }
    }

    setInterval(revisarEstadoEvaluacion, 1000);
    revisarEstadoEvaluacion();
  });
