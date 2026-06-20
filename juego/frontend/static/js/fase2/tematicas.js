document.addEventListener("DOMContentLoaded", () => {
  inicializarCarruselTematicas();
  inicializarTematicas();
  inicializarObjetoCamara();
  inicializarMusicaDesafios();
});

function inicializarCarruselTematicas() {
  const track = document.getElementById("themesTrack");
  const prev = document.querySelector(".carousel-btn.prev");
  const next = document.querySelector(".carousel-btn.next");

  function moverCarrusel(direccion) {
    if (!track) return;

    const primera = track.querySelector(".theme-card");
    if (!primera) return;

    const ancho = primera.offsetWidth + 24;
    track.scrollLeft += direccion * ancho;
  }

  prev?.addEventListener("click", (event) => {
    event.preventDefault();
    moverCarrusel(-1);
  });

  next?.addEventListener("click", (event) => {
    event.preventDefault();
    moverCarrusel(1);
  });
}

function inicializarTematicas() {
  const routesEl = document.getElementById("routes");

  const sesionId = routesEl?.dataset?.sesionId;
  const grupoId = routesEl?.dataset?.grupoId;
  const guardarTematicaUrl = routesEl?.dataset?.guardarTematicaUrl;
  const desafiosUrl = routesEl?.dataset?.desafiosUrl;

  const cards = Array.from(document.querySelectorAll(".theme-card"));
  const botonesSeleccion = document.querySelectorAll(".btn.select");

  const timerTematica = document.getElementById("timerTematica");
  const overlayInicio = document.getElementById("inicio-fase-overlay");
  const contenidoTematicas = document.getElementById("contenidoTematicas");
  const btnListoTematica = document.getElementById("btnListoTematica");
  const contadorListosTematica = document.getElementById("contadorListosTematica");
  const textoEsperaTematica = document.getElementById("textoEsperaTematica");

  let enviando = false;
  let yaListoTematica = false;
  let timerTematicaSolicitado = false;
  let ultimoListos = 0;
  let ultimoTotal = 0;
  let temaSeleccionadoActual = routesEl?.dataset?.temaActual || "";

  function tJuego(clave, fallback = "") {
    const idioma = window.i18nJuego?.obtenerIdioma?.() || "es";
    return window.i18nJuego?.traducciones?.[idioma]?.[clave] || fallback;
  }

  function textoGruposListos(listos, total) {
    return `${listos}/${total} ${tJuego("tematicas_grupos_listos", "grupos listos")}`;
  }

  function textoEsperando() {
    return tJuego("tematicas_boton_esperando", "Esperando...");
  }

  function textoListo() {
    return tJuego("tematicas_boton_listo", "⚡ Listo para comenzar");
  }

  function textoElegir() {
    return tJuego("tematicas_elegir", "Elegir");
  }

  function textoSeleccionado() {
    return tJuego("tematicas_seleccionado", "Seleccionado ✅");
  }

  function textoEsperaEquipos() {
    return tJuego("tematicas_esperando", "Esperando a los demás equipos...");
  }

  function formatearTiempo(segundos) {
    segundos = Math.max(Number(segundos || 0), 0);

    const min = Math.floor(segundos / 60);
    const seg = segundos % 60;

    return `${min}:${String(seg).padStart(2, "0")}`;
  }

  function habilitarTematicas() {
    if (overlayInicio) overlayInicio.classList.add("overlay-hidden");
    if (contenidoTematicas) contenidoTematicas.classList.remove("blur-tematicas");
  }

  function bloquearTematicas() {
    if (overlayInicio) overlayInicio.classList.remove("overlay-hidden");
    if (contenidoTematicas) contenidoTematicas.classList.add("blur-tematicas");
  }

  function getCSRFToken() {
    const name = "csrftoken=";
    const parts = document.cookie.split(";");

    for (let c of parts) {
      c = c.trim();

      if (c.startsWith(name)) {
        return decodeURIComponent(c.substring(name.length));
      }
    }

    return "";
  }

  async function iniciarTimerTematica() {
    if (!sesionId) return;

    try {
      await fetch(`/sesion/${sesionId}/iniciar-timer-inicio-fase/`, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCSRFToken(),
        },
        body: JSON.stringify({}),
      });
    } catch (error) {
      console.error("Error iniciando timer:", error);
      timerTematicaSolicitado = false;
    }
  }

  function todosListosSegunData(data) {
    const total = Number(data.totalGrupos || 0);
    const listos = Number(data.gruposListosF2Tematicas || 0);

    if (data.todosListosF2Tematicas) return true;

    return total > 0 && listos >= total;
  }

  async function actualizarTimerTematica() {
    if (!sesionId || !timerTematica) return;

    try {
      const res = await fetch(`/sesion/${sesionId}/estado/`, {
        cache: "no-store",
        credentials: "same-origin",
      });

      if (!res.ok) return;

      const data = await res.json();

      timerTematica.textContent = formatearTiempo(data.segundosRestantes);

      ultimoListos = Number(data.gruposListosF2Tematicas || 0);
      ultimoTotal = Number(data.totalGrupos || 0);

      if (contadorListosTematica) {
        contadorListosTematica.textContent = textoGruposListos(ultimoListos, ultimoTotal);
      }

      const miGrupo = (data.grupos || []).find((grupo) => Number(grupo.id) === Number(grupoId));

      if (miGrupo && miGrupo.listoF2Tematicas) {
        yaListoTematica = true;

        if (btnListoTematica) {
          btnListoTematica.disabled = true;
          btnListoTematica.textContent = textoEsperando();
        }

        if (textoEsperaTematica) {
          textoEsperaTematica.textContent = textoEsperaEquipos();
        }
      }

      if (todosListosSegunData(data)) {
        habilitarTematicas();

        if (!data.timerCorriendo && !timerTematicaSolicitado) {
          timerTematicaSolicitado = true;
          iniciarTimerTematica();
        }
      } else {
        bloquearTematicas();
      }

      if (data.faseActual && data.faseActual !== "f2_tematicas" && data.rutaAlumno) {
        window.location.href = data.rutaAlumno;
      }
    } catch (error) {
      console.error("Error actualizando timer:", error);
    }
  }

  async function marcarListoTematica() {
    if (yaListoTematica || !grupoId) return;

    yaListoTematica = true;

    if (btnListoTematica) {
      btnListoTematica.disabled = true;
      btnListoTematica.textContent = textoEsperando();
    }

    if (textoEsperaTematica) {
      textoEsperaTematica.textContent = textoEsperaEquipos();
    }

    try {
      const res = await fetch(`/grupo/${grupoId}/listo/`, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCSRFToken(),
        },
        body: JSON.stringify({
          fase: "f2_tematicas",
        }),
      });

      const data = await res.json();

      ultimoListos = Number(data.gruposListosF2Tematicas || data.listos || 0);
      ultimoTotal = Number(data.totalGrupos || data.total || 0);

      if (contadorListosTematica) {
        contadorListosTematica.textContent = textoGruposListos(ultimoListos, ultimoTotal);
      }

      if (data.todos_listos || (ultimoTotal > 0 && ultimoListos >= ultimoTotal)) {
        habilitarTematicas();

        if (!timerTematicaSolicitado) {
          timerTematicaSolicitado = true;
          iniciarTimerTematica();
        }
      }
    } catch (error) {
      console.error("Error marcando listo:", error);

      yaListoTematica = false;

      if (btnListoTematica) {
        btnListoTematica.disabled = false;
        btnListoTematica.textContent = textoListo();
      }
    }
  }

  function marcarTema(slug) {
    temaSeleccionadoActual = (slug || "").trim().toLowerCase();

    cards.forEach((card) => {
      const activo = (card.dataset.slug || "").trim().toLowerCase() === temaSeleccionadoActual;

      card.classList.toggle("selected", activo);

      const btn = card.querySelector(".btn.select");

      if (btn) {
        btn.textContent = activo ? textoSeleccionado() : textoElegir();
      }
    });
  }

  async function guardarTema(slug) {
    if (enviando) return;

    enviando = true;
    marcarTema(slug);

    botonesSeleccion.forEach((boton) => {
      boton.disabled = true;
    });

    try {
      const res = await fetch(guardarTematicaUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCSRFToken(),
        },
        credentials: "same-origin",
        body: JSON.stringify({
          tema: slug,
        }),
      });

      const data = await res.json();

      if (!res.ok || !data.ok) {
        throw new Error(data.error || "No se pudo guardar.");
      }

      window.location.href = data.redirect_url || desafiosUrl;
    } catch (error) {
      alert(error.message);

      botonesSeleccion.forEach((boton) => {
        boton.disabled = false;
      });

      marcarTema("");
      enviando = false;
    }
  }

  botonesSeleccion.forEach((boton) => {
    boton.addEventListener("click", () => {
      guardarTema(boton.dataset.slug);
    });
  });

  if (temaSeleccionadoActual) {
    marcarTema(temaSeleccionadoActual);
  } else {
    marcarTema("");
  }

  if (btnListoTematica) {
    btnListoTematica.addEventListener("click", marcarListoTematica);
  }

  window.addEventListener("idiomaJuegoCambiado", () => {
    if (contadorListosTematica) {
      contadorListosTematica.textContent = textoGruposListos(ultimoListos, ultimoTotal);
    }

    if (btnListoTematica) {
      btnListoTematica.textContent = btnListoTematica.disabled ? textoEsperando() : textoListo();
    }

    if (textoEsperaTematica) {
      textoEsperaTematica.textContent = textoEsperaEquipos();
    }

    marcarTema(temaSeleccionadoActual);
  });

  bloquearTematicas();

  setInterval(actualizarTimerTematica, 1000);
  actualizarTimerTematica();
}

function inicializarObjetoCamara() {
  const routesEl = document.getElementById("routes");

  const sesionId = routesEl?.dataset?.sesionId;
  const grupoId = routesEl?.dataset?.grupoId;

  const camaraTrigger = document.getElementById("objetoCamaraTrigger");
  const camaraOverlay = document.getElementById("objetoCamaraOverlay");
  const camaraClose = document.getElementById("objetoCamaraClose");

  const storageCamara = `objeto_camara_tematicas_usado_${sesionId}_${grupoId}`;

  if (localStorage.getItem(storageCamara) === "1" && camaraTrigger) {
    camaraTrigger.classList.add("oculto");
  }

  function abrirCamara() {
    if (!camaraOverlay) return;

    camaraOverlay.classList.add("activo");
    camaraOverlay.setAttribute("aria-hidden", "false");
  }

  function cerrarCamara() {
    if (!camaraOverlay) return;

    camaraOverlay.classList.remove("activo");
    camaraOverlay.setAttribute("aria-hidden", "true");

    if (camaraTrigger) {
      camaraTrigger.classList.add("oculto");
    }

    localStorage.setItem(storageCamara, "1");
  }

  camaraTrigger?.addEventListener("click", abrirCamara);
  camaraClose?.addEventListener("click", cerrarCamara);

  camaraOverlay?.addEventListener("click", (event) => {
    if (event.target === camaraOverlay) {
      cerrarCamara();
    }
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