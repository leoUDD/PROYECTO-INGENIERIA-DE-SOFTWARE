(function () {
  document.addEventListener("DOMContentLoaded", () => {
    const pageData = document.body.dataset;
    const sesionId = pageData.sesionId || "";
    const grupoId = pageData.grupoId || "";
    const csrfToken = pageData.csrfToken || "";
    const pantallaEsperaUrl = pageData.pantallaEsperaUrl || "/pantalla-espera/";

    const box = document.getElementById("textoGuardado");
    const timerEl = document.getElementById("timer");
    const alarm = document.getElementById("alarmAudio");
    const btnIniciar = document.getElementById("btnIniciarPresentacion");

    let ultimoSegundo = null;
    let alarmaDisparada = false;
    let redirigiendoPitch = false;
    let pollingEstadoPresentacion = null;

    function tPitch(clave, fallback) {
      try {
        const idioma = window.i18nJuego?.obtenerIdioma?.() || "es";
        return window.i18nJuego?.traducciones?.[idioma]?.[clave] || fallback;
      } catch (e) {
        return fallback;
      }
    }

    function escapeHTML(valor) {
      return String(valor || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
    }

    function actualizarTextoPropio(texto) {
      if (!box) return;

      if (texto && texto.trim()) {
        box.innerHTML = `<div class="prewrap">${escapeHTML(texto)}</div>`;
      } else {
        box.innerHTML = `<em>${tPitch("presentar_pitch_sin_texto", "No se encontró texto guardado. Vuelve a la etapa anterior y escribe tu pitch.")}</em>`;
      }
    }

    function reproducirAlarmaSuave() {
      if (!alarm) return;

      try {
        alarm.currentTime = 0;
        alarm.play().catch(() => {});
      } catch (_) {}
    }

    function formatearTiempo(totalSegundos) {
      const segundos = Math.max(0, Number(totalSegundos || 0));
      const min = String(Math.floor(segundos / 60)).padStart(2, "0");
      const sec = String(segundos % 60).padStart(2, "0");
      return `${min}:${sec}`;
    }

    function actualizarTimer(segundos) {
      if (!timerEl) return;

      const valor = Math.max(0, Number(segundos || 0));
      timerEl.textContent = formatearTiempo(valor);
      timerEl.dataset.seconds = valor;

      if (ultimoSegundo !== null && valor > 0) {
        alarmaDisparada = false;
      }

      if (valor === 0 && !alarmaDisparada && ultimoSegundo !== 0) {
        reproducirAlarmaSuave();
        alarmaDisparada = true;
      }

      ultimoSegundo = valor;
    }

    window.presentarPitchUI = {
      actualizarPitchPropio(texto) {
        actualizarTextoPropio(texto);
      },
      actualizarTimer(segundos) {
        actualizarTimer(segundos);
      }
    };

    function actualizarTextosEstaticosPitch() {
      document.title = tPitch("presentar_pitch_document_title", "Misión Emprende UDD — Presentar Pitch");

      const img = document.getElementById("grupoActualAlumnoFoto");
      if (img) {
        img.alt = tPitch("presentar_pitch_foto_alt", "Foto del lego del grupo que está presentando");
      }

      const aside = document.querySelector(".timer-panel");
      if (aside) {
        aside.setAttribute("aria-label", tPitch("presentar_pitch_aria_temporizador", "Temporizador de Pitch"));
      }
    }

    function renderOrdenAlumno(ordenPitch, grupoActual) {
      const lista = document.getElementById("ordenPitchAlumno");
      if (!lista) return;

      if (!ordenPitch || !ordenPitch.length) {
        lista.innerHTML = `<li>${tPitch("presentar_pitch_esperando_sorteo", "Esperando sorteo...")}</li>`;
        return;
      }

      lista.innerHTML = ordenPitch.map((item) => {
        const esActual = grupoActual && String(grupoActual.id) === String(item.id);
        const nombre = escapeHTML(item.nombre || "");
        const orden = escapeHTML(item.orden || "");
        const flecha = esActual ? ` ${tPitch("presentar_pitch_presentando_flecha", "← presentando")}` : "";

        return `<li class="${esActual ? "actual" : ""}">${orden}. ${nombre}${flecha}</li>`;
      }).join("");
    }

    function renderFotoOTexto(grupoActual) {
      const foto = document.getElementById("grupoActualAlumnoFoto");
      const sinFoto = document.getElementById("grupoActualAlumnoSinFoto");

      if (!foto || !sinFoto) return;

      if (grupoActual && grupoActual.fotoLego) {
        foto.src = grupoActual.fotoLego;
        foto.classList.remove("is-hidden");
        sinFoto.classList.add("is-hidden");
        return;
      }

      foto.removeAttribute("src");
      foto.classList.add("is-hidden");
      sinFoto.classList.remove("is-hidden");
      sinFoto.textContent = tPitch("presentar_pitch_sin_foto", "Este equipo no subió foto de su solución LEGO.");
    }

    function renderBotonInicio(data) {
      const wrap = document.getElementById("pitchStartWrap");
      const btn = document.getElementById("btnIniciarPresentacion");
      const help = document.getElementById("pitchStartHelp");

      if (!wrap || !btn || !help) return;

      const grupoActual = data.grupoActual;
      const soyGrupoActual = grupoActual && String(grupoActual.id) === String(grupoId);
      const timerCorriendo = Boolean(data.timerCorriendo);
      const tiempo = Number(data.segundosRestantes || 0);

      if (!soyGrupoActual) {
        wrap.classList.add("is-hidden");
        return;
      }

      wrap.classList.remove("is-hidden");

      if (timerCorriendo) {
        btn.disabled = true;
        btn.textContent = tPitch("presentar_pitch_boton_presentando", "Presentando...");
        help.textContent = tPitch("presentar_pitch_help_en_curso", "Tu presentación está en curso.");
        return;
      }

      if (tiempo <= 0) {
        btn.disabled = true;
        btn.textContent = tPitch("presentar_pitch_boton_tiempo_finalizado", "Tiempo finalizado");
        help.textContent = tPitch("presentar_pitch_help_esperando_evaluacion", "Esperando cambio a evaluación.");
        return;
      }

      btn.disabled = false;
      btn.textContent = tPitch("presentar_pitch_boton_iniciar", "⚡ Iniciar presentación");
      help.innerHTML = tPitch(
        "presentar_pitch_help_iniciar_html",
        "Tu equipo está presentando ahora. Presionen <strong>“Iniciar presentación”</strong> para comenzar el temporizador."
      );
    }

    function renderEstadoPresentacion(data) {
      actualizarTextosEstaticosPitch();

      if (data.faseActual && data.faseActual !== "f4_presentacion_pitch") {
        if (!redirigiendoPitch) {
          redirigiendoPitch = true;
          window.location.replace(data.rutaAlumno || pantallaEsperaUrl);
        }
        return;
      }

      const grupoActual = data.grupoActual;
      const nombre = document.getElementById("grupoActualAlumnoNombre");
      const orden = document.getElementById("grupoActualAlumnoOrden");

      if (nombre) {
        nombre.textContent = grupoActual
          ? grupoActual.nombre
          : tPitch("presentar_pitch_esperando_sorteo", "Esperando sorteo...");
      }

      if (orden) {
        orden.textContent = grupoActual
          ? `${tPitch("presentar_pitch_orden_label", "Orden")} ${grupoActual.orden}`
          : "-";
      }

      renderFotoOTexto(grupoActual);
      actualizarTimer(data.segundosRestantes);
      actualizarTextoPropio(data.miPitch || "");
      renderOrdenAlumno(data.ordenPitch, grupoActual);
      renderBotonInicio(data);
    }

    async function cargarEstadoPresentacion() {
      if (redirigiendoPitch || !sesionId) return;

      try {
        const res = await fetch(`/sesion/${sesionId}/estado-presentacion/`, {
          credentials: "same-origin",
          cache: "no-store"
        });

        const contentType = res.headers.get("content-type") || "";

        if (!contentType.includes("application/json")) {
          console.warn("estado-presentacion no devolvió JSON", res.status);
          return;
        }

        const data = await res.json();

        if (!res.ok || !data.ok) {
          console.warn("Estado presentación inválido", data);
          return;
        }

        renderEstadoPresentacion(data);
      } catch (error) {
        console.error("Error cargando estado de presentación:", error);
      }
    }

    async function iniciarPresentacion() {
      const btn = document.getElementById("btnIniciarPresentacion");
      const help = document.getElementById("pitchStartHelp");

      if (!btn || !sesionId) return;

      btn.disabled = true;
      btn.textContent = tPitch("presentar_pitch_boton_iniciando", "Iniciando...");

      try {
        const res = await fetch(`/sesion/${sesionId}/iniciar-presentacion/`, {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken
          },
          body: JSON.stringify({})
        });

        const contentType = res.headers.get("content-type") || "";
        if (!contentType.includes("application/json")) {
          throw new Error(tPitch("presentar_pitch_error_no_iniciar", "No se pudo iniciar la presentación."));
        }

        const data = await res.json();

        if (!res.ok || !data.ok) {
          throw new Error(data.error || tPitch("presentar_pitch_error_no_iniciar", "No se pudo iniciar la presentación."));
        }

        renderEstadoPresentacion(data);
      } catch (error) {
        console.error("Error iniciando presentación:", error);

        btn.disabled = false;
        btn.textContent = tPitch("presentar_pitch_boton_iniciar", "⚡ Iniciar presentación");

        if (help) {
          help.textContent = error.message || tPitch("presentar_pitch_error_temporizador", "No se pudo iniciar el temporizador.");
        }
      }
    }

    actualizarTextosEstaticosPitch();

    if (timerEl) {
      const inicial = Math.max(0, Number(timerEl.dataset.seconds || 90));
      actualizarTimer(inicial);
    }

    if (btnIniciar) {
      btnIniciar.addEventListener("click", iniciarPresentacion);
    }

    window.addEventListener("idiomaJuegoCambiado", () => {
      actualizarTextosEstaticosPitch();
      cargarEstadoPresentacion();
    });

    cargarEstadoPresentacion();
    pollingEstadoPresentacion = setInterval(cargarEstadoPresentacion, 1000);

    window.addEventListener("beforeunload", () => {
      if (pollingEstadoPresentacion) {
        clearInterval(pollingEstadoPresentacion);
      }
    });
  });
})();
