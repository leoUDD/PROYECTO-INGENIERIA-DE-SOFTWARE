function obtenerConfigLego() {
  const body = document.body;

  return {
    sesionId: body.dataset.sesionId || "",
    grupoId: body.dataset.grupoId || "",
    csrfToken: body.dataset.csrfToken || "",
    tiempoInicial: Number(body.dataset.tiempoInicial || 15),
    aplicarResultadoRuletaUrl: body.dataset.aplicarResultadoRuletaUrl || "",
  };
}

function tLego(clave, fallback = "") {
  const idioma = window.i18nJuego?.obtenerIdioma?.() || "es";
  return window.i18nJuego?.traducciones?.[idioma]?.[clave] || fallback;
}

function obtenerOpcionesRuleta() {
  const nodo = document.getElementById("opciones-ruleta-data");

  if (!nodo) return [];

  try {
    return JSON.parse(nodo.textContent || "[]");
  } catch (error) {
    console.error("No se pudieron leer las opciones de la ruleta LEGO:", error);
    return [];
  }
}

function inicializarPanelDesafio() {
  const toggle = document.getElementById("desafioToggle");
  const body = document.getElementById("desafioBody");
  const icono = document.getElementById("desafioIcono");

  if (!toggle || !body || !icono) return;

  toggle.addEventListener("click", () => {
    const abierto = !body.hasAttribute("hidden");

    if (abierto) {
      body.setAttribute("hidden", "hidden");
      icono.textContent = "▼";
    } else {
      body.removeAttribute("hidden");
      icono.textContent = "▲";
    }
  });
}

function inicializarIdeasBubblemap() {
  const config = obtenerConfigLego();
  const list = document.getElementById("ideasList");
  const storageKey = `bubblemap_data_v3_sesion_${config.sesionId}_grupo_${config.grupoId}`;

  function cargarIdeasBubblemap() {
    if (!list) return;

    list.innerHTML = "";

    const saved = JSON.parse(localStorage.getItem(storageKey) || "{}");
    const ideas = [];

    Object.values(saved.burbujas || {}).forEach((valor) => {
      if (String(valor || "").trim()) ideas.push(String(valor).trim());
    });

    (saved.otros || []).forEach((valor) => {
      if (String(valor || "").trim()) ideas.push(String(valor).trim());
    });

    if (ideas.length === 0) {
      list.innerHTML = `<li>${tLego("lego_ideas_vacias", "No se ingresaron ideas.")}</li>`;
      return;
    }

    ideas.forEach((texto) => {
      const li = document.createElement("li");
      li.textContent = texto;
      list.appendChild(li);
    });
  }

  cargarIdeasBubblemap();
  window.addEventListener("idiomaJuegoCambiado", cargarIdeasBubblemap);
}

function inicializarFaseLego() {
  const config = obtenerConfigLego();

  const boton = document.getElementById("btn-listo-fase");
  const textoEspera = document.getElementById("texto-espera-fase");
  const contador = document.getElementById("contador-listos-fase");
  const timerEl = document.getElementById("timer");
  const modalFin = document.getElementById("modal-fin");
  const alarmAudio = document.getElementById("alarm-audio");
  const overlay = document.getElementById("inicio-fase-overlay");

  let timerLiberadoTrasCountdown = false;
  let countdownMostrado = false;
  let countdownEnCurso = false;

  const blurTargets = [
    document.getElementById("legoLogo"),
    document.getElementById("legoTitle"),
    document.getElementById("ruletaLegoCard"),
    document.getElementById("desafioPanel"),
    document.getElementById("legoSubtitle"),
    document.getElementById("ideasList"),
    document.getElementById("legoBody"),
    document.getElementById("timer"),
    document.getElementById("fotoPanel"),
    document.getElementById("astroLegoTrigger"),
  ];

  let timeLeft = config.tiempoInicial;
  let timerInterval = null;
  let timerStartedByProfesor = false;
  let modalMostrado = false;
  let redirigiendo = false;
  let timerRealSolicitado = false;

  function textoGruposListos(listos, total) {
    return `${listos}/${total} ${tLego("lego_grupos_listos", "grupos listos")}`;
  }

  function textoDetalleLego(conFoto, sinFoto) {
    return `${conFoto} ${tLego("lego_con_foto", "con foto")} · ${sinFoto} ${tLego("lego_sin_foto_detalle", "sin foto")}`;
  }

  function textoBotonListo() {
    return tLego("lego_boton_listo", "⚡ Listo para comenzar");
  }

  function textoEsperando() {
    return tLego("lego_boton_esperando", "Esperando...");
  }

  function textoEsperandoEquipos() {
    return tLego("lego_esperando_equipos", "Esperando a los demás equipos...");
  }

  function aplicarTraduccionDinamicaLego() {
    if (boton) boton.textContent = boton.disabled ? textoEsperando() : textoBotonListo();

    if (textoEspera) {
      const texto = (textoEspera.textContent || "").toLowerCase();
      textoEspera.textContent = texto.includes("no se pudo") || texto.includes("could not")
        ? tLego("lego_error_registro", "No se pudo registrar. Intenta nuevamente.")
        : textoEsperandoEquipos();
    }

    if (contador) {
      const match = (contador.textContent || "").match(/(\d+)\/(\d+)/);
      if (match) contador.textContent = textoGruposListos(match[1], match[2]);
    }

    const estado = document.getElementById("estadoGruposLego");
    const detalle = document.getElementById("detalleGruposLego");

    if (estado) {
      const match = (estado.textContent || "").match(/(\d+)\/(\d+)/);
      if (match) estado.textContent = textoGruposListos(match[1], match[2]);
    }

    if (detalle) {
      const match = (detalle.textContent || "").match(/(\d+).*?(\d+)/);
      if (match) detalle.textContent = textoDetalleLego(match[1], match[2]);
    }

    const botonGuardar = document.getElementById("buttonGuardarFoto");
    if (botonGuardar && !botonGuardar.disabled) {
      botonGuardar.textContent = tLego("lego_guardar_continuar", "Guardar y continuar");
    }
  }

  function activarFase() {
    blurTargets.forEach((el) => {
      if (!el) return;
      el.classList.remove("blur-target-bloqueado", "timer-esperando");
      el.classList.add("blur-target-activo");
    });

    if (overlay) overlay.classList.add("overlay-hidden");
  }

  function bloquearFase() {
    blurTargets.forEach((el) => {
      if (!el) return;
      el.classList.remove("blur-target-activo");
      el.classList.add("blur-target-bloqueado");
    });

    if (timerEl) timerEl.classList.add("timer-esperando");
    if (overlay) overlay.classList.remove("overlay-hidden");
  }

  function renderTimer() {
    if (!timerEl) return;

    const segundos = Math.max(0, Number(timeLeft) || 0);
    timerEl.textContent = `${String(Math.floor(segundos / 60)).padStart(2, "0")}:${String(segundos % 60).padStart(2, "0")}`;
  }

  function pauseTimerLocally() {
    if (!timerInterval) return;

    clearInterval(timerInterval);
    timerInterval = null;
  }

  function mostrarModalFin() {
    if (modalMostrado) return;

    modalMostrado = true;

    try {
      if (alarmAudio) {
        alarmAudio.currentTime = 0;
        alarmAudio.play();
      }
    } catch (error) {}

    if (modalFin) modalFin.style.display = "flex";

    const musicaLego = document.getElementById("musica-lego");
    const btnMusica = document.getElementById("btn-musica-lego");

    if (musicaLego) musicaLego.pause();
    if (btnMusica) btnMusica.style.display = "none";
  }

  async function iniciarTimerRealDespuesCountdown() {
    if (timerRealSolicitado) return;

    timerRealSolicitado = true;

    try {
      const res = await fetch(`/sesion/${config.sesionId}/iniciar-timer-inicio-fase/`, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": config.csrfToken,
        },
        body: JSON.stringify({ fase: "f3_lego" }),
      });

      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error(data.error || "Error timer");

      const segundosRestantes = Number(data.segundosRestantes);
      if (!Number.isNaN(segundosRestantes)) {
        timeLeft = segundosRestantes;
        renderTimer();
      }
    } catch (error) {
      console.error("Error timer lego:", error);
      timerRealSolicitado = false;
    }
  }

  function startTimer() {
    if (timerInterval) return;

    renderTimer();

    timerInterval = setInterval(() => {
      timeLeft--;
      renderTimer();

      if (timeLeft <= 0) {
        pauseTimerLocally();
        mostrarModalFin();
      }
    }, 1000);
  }

  function actualizarEstadoGrupos(data) {
    const estado = document.getElementById("estadoGruposLego");
    const detalle = document.getElementById("detalleGruposLego");

    if (!estado || !detalle) return;

    estado.textContent = textoGruposListos(data.gruposListosF3Lego || 0, data.totalGrupos || 0);
    detalle.textContent = textoDetalleLego(data.gruposConFotoLego || 0, data.gruposSinFotoLego || 0);
  }

  function procesarEstadoSesion(data) {
    if (!data) return;

    actualizarEstadoGrupos(data);

    if (contador) {
      contador.textContent = textoGruposListos(data.listosInicio || 0, data.totalListosInicio || 0);
    }

    const miGrupo = (data.grupos || []).find((grupo) => Number(grupo.id) === Number(config.grupoId));

    if (miGrupo?.listoInicioF3 && boton) {
      boton.disabled = true;
      boton.textContent = textoEsperando();
      if (textoEspera) textoEspera.textContent = textoEsperandoEquipos();
    }

    if (data.faseActual && data.faseActual !== "f3_lego") {
      if (data.rutaAlumno && window.location.pathname !== data.rutaAlumno) {
        redirigiendo = true;
        window.location.href = data.rutaAlumno;
      }
      return;
    }

    if (data.inicioFaseHabilitado) {
      if (!countdownMostrado && !countdownEnCurso) {
        countdownEnCurso = true;

        if (!window.oaiCountdown?.run) {
          countdownMostrado = true;
          countdownEnCurso = false;
          timerLiberadoTrasCountdown = true;
          activarFase();
          iniciarTimerRealDespuesCountdown();
          return;
        }

        window.oaiCountdown.run(async () => {
          countdownMostrado = true;
          countdownEnCurso = false;
          timerLiberadoTrasCountdown = true;
          await iniciarTimerRealDespuesCountdown();
          activarFase();
        });
        return;
      }

      if (countdownMostrado && !countdownEnCurso) activarFase();
    } else {
      countdownMostrado = false;
      countdownEnCurso = false;
      timerLiberadoTrasCountdown = false;
      timerRealSolicitado = false;
      bloquearFase();
    }

    const segundosRestantes = Number(data.segundosRestantes);

    if ((!timerStartedByProfesor || !data.timerCorriendo) && !Number.isNaN(segundosRestantes)) {
      if (!countdownEnCurso && !timerLiberadoTrasCountdown) {
        timeLeft = segundosRestantes;
        renderTimer();
      }
    }

    if (!timerStartedByProfesor && data.timerCorriendo && data.inicioFaseHabilitado) {
      if (!countdownMostrado || countdownEnCurso || !timerLiberadoTrasCountdown) return;

      timerStartedByProfesor = true;

      if (!Number.isNaN(segundosRestantes) && segundosRestantes >= 0) {
        timeLeft = segundosRestantes;
        renderTimer();
      }

      startTimer();
      return;
    }

    if (timerStartedByProfesor && !data.timerCorriendo) {
      pauseTimerLocally();

      if (!Number.isNaN(segundosRestantes) && segundosRestantes >= 0) {
        timeLeft = segundosRestantes;
        renderTimer();
      }

      timerStartedByProfesor = false;
    }

    if (Number(data.segundosRestantes) <= 0) mostrarModalFin();

    if (data.todosListosF3Lego && data.rutaAlumno) {
      redirigiendo = true;
      window.location.href = data.rutaAlumno;
    }
  }

  async function revisarEstadoProfesor() {
    if (redirigiendo) return;

    try {
      const res = await fetch(`/sesion/${config.sesionId}/estado/`, {
        credentials: "same-origin",
        cache: "no-store",
      });

      if (!res.ok) return;

      const data = await res.json();
      procesarEstadoSesion(data);
    } catch (error) {
      console.error("Error sincronizando lego:", error);
    }
  }

  if (boton) {
    boton.addEventListener("click", async () => {
      boton.disabled = true;
      boton.textContent = textoEsperando();

      try {
        const res = await fetch(`/grupo/${config.grupoId}/listo/`, {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": config.csrfToken,
          },
          body: JSON.stringify({ fase: "inicio_f3" }),
        });

        const data = await res.json();
        if (!res.ok || !data.ok) throw new Error(data.error || tLego("lego_error_listo", "No se pudo marcar listo."));

        if (contador) contador.textContent = textoGruposListos(data.listos || 0, data.total || 0);
        if (textoEspera) textoEspera.textContent = textoEsperandoEquipos();

        revisarEstadoProfesor();
      } catch (error) {
        console.error("Error marcando listo:", error);
        boton.disabled = false;
        boton.textContent = textoBotonListo();
        if (textoEspera) textoEspera.textContent = tLego("lego_error_registro", "No se pudo registrar. Intenta nuevamente.");
      }
    });
  }

  window.addEventListener("idiomaJuegoCambiado", aplicarTraduccionDinamicaLego);

  bloquearFase();
  renderTimer();
  aplicarTraduccionDinamicaLego();
  revisarEstadoProfesor();
  setInterval(revisarEstadoProfesor, 1500);
}

function inicializarFotoLego() {
  const inputFoto = document.getElementById("foto_lego");
  const sinFoto = document.getElementById("sin_foto_lego");
  const previewWrapper = document.getElementById("previewWrapper");
  const previewImg = document.getElementById("previewImg");
  const buttonGuardarFoto = document.getElementById("buttonGuardarFoto");
  const errorFoto = document.getElementById("errorFoto");
  const formFoto = document.querySelector("#modal-fin form");

  let yaEnviado = false;

  function actualizarEstadoBoton() {
    const hayArchivo = inputFoto && inputFoto.files && inputFoto.files.length > 0;
    const marcoSinFoto = sinFoto && sinFoto.checked;

    if (buttonGuardarFoto) buttonGuardarFoto.disabled = !(hayArchivo || marcoSinFoto) || yaEnviado;
    if (errorFoto) errorFoto.style.display = "none";

    if (marcoSinFoto && inputFoto && previewWrapper && previewImg) {
      inputFoto.value = "";
      previewWrapper.classList.remove("visible");
      previewImg.removeAttribute("src");
    }
  }

  if (inputFoto) {
    inputFoto.addEventListener("change", (event) => {
      const file = event.target.files && event.target.files[0];

      if (sinFoto) sinFoto.checked = false;

      if (!file) {
        if (previewWrapper) previewWrapper.classList.remove("visible");
        if (previewImg) previewImg.removeAttribute("src");
        actualizarEstadoBoton();
        return;
      }

      if (previewImg) previewImg.src = URL.createObjectURL(file);
      if (previewWrapper) previewWrapper.classList.add("visible");
      actualizarEstadoBoton();
    });
  }

  if (sinFoto) sinFoto.addEventListener("change", actualizarEstadoBoton);

  if (formFoto) {
    formFoto.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (yaEnviado) return;

      const hayArchivo = inputFoto && inputFoto.files && inputFoto.files.length > 0;
      const marcoSinFoto = sinFoto && sinFoto.checked;

      if (!hayArchivo && !marcoSinFoto) {
        if (errorFoto) {
          errorFoto.style.display = "block";
          errorFoto.textContent = tLego("lego_error_foto", "Debes subir una foto o marcar que no pudieron subirla.");
        }
        return;
      }

      const formData = new FormData(formFoto);

      try {
        const res = await fetch(window.location.href, {
          method: "POST",
          body: formData,
          headers: {
            "X-Requested-With": "XMLHttpRequest",
          },
        });

        const data = await res.json();
        if (!data.ok) throw new Error(data.error || tLego("lego_error_guardar_foto", "Error guardando"));

        yaEnviado = true;

        if (inputFoto) inputFoto.disabled = true;
        if (sinFoto) sinFoto.disabled = true;
        if (buttonGuardarFoto) {
          buttonGuardarFoto.disabled = true;
          buttonGuardarFoto.textContent = tLego("lego_listo", "¡Listo!");
        }

        const estado = document.getElementById("estadoGruposLego");
        const detalle = document.getElementById("detalleGruposLego");

        if (estado) estado.textContent = `${data.gruposListosF3Lego || 0}/${data.totalGrupos || 0} ${tLego("lego_grupos_listos", "grupos listos")}`;
        if (detalle) detalle.textContent = `${data.gruposConFotoLego || 0} ${tLego("lego_con_foto", "con foto")} · ${data.gruposSinFotoLego || 0} ${tLego("lego_sin_foto_detalle", "sin foto")}`;
      } catch (error) {
        console.error(error);
        if (errorFoto) {
          errorFoto.style.display = "block";
          errorFoto.textContent = error.message;
        }
      }
    });
  }

  window.addEventListener("idiomaJuegoCambiado", () => {
    if (!yaEnviado && buttonGuardarFoto) buttonGuardarFoto.textContent = tLego("lego_guardar_continuar", "Guardar y continuar");
    if (errorFoto && errorFoto.style.display !== "none") errorFoto.textContent = tLego("lego_error_foto", "Debes subir una foto o marcar que no pudieron subirla.");
  });
}

function inicializarAstroLego() {
  const config = obtenerConfigLego();

  const astroTrigger = document.getElementById("astroLegoTrigger");
  const astroOverlay = document.getElementById("astroLegoOverlay");
  const astroClose = document.getElementById("astroLegoClose");
  const astroFeedback = document.getElementById("astroLegoFeedback");
  const astroOpciones = document.querySelectorAll(".astro-lego-opcion");
  const storageAstroLego = `astro_lego_pregunta_usada_${config.sesionId}_${config.grupoId}`;

  let respondido = localStorage.getItem(storageAstroLego) === "1";

  if (respondido && astroTrigger) astroTrigger.classList.add("oculto");

  astroTrigger?.addEventListener("click", () => {
    if (!astroOverlay || respondido) return;

    astroOverlay.classList.add("activo");
    astroOverlay.setAttribute("aria-hidden", "false");
  });

  astroOpciones.forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (respondido) return;

      respondido = true;
      localStorage.setItem(storageAstroLego, "1");

      const correcta = btn.dataset.correcta === "true";

      astroOpciones.forEach((opcion) => {
        opcion.disabled = true;
        if (opcion.dataset.correcta === "true") opcion.classList.add("correcta");
      });

      if (correcta) {
        btn.classList.add("correcta");

        if (astroFeedback) {
          astroFeedback.className = "astro-lego-feedback visible ok";
          astroFeedback.textContent = tLego("lego_astro_feedback_ok", "¡Correcto! La respuesta era Trabajo en equipo → Empatía → Creatividad. Toma tus 2 tokens.");
        }

        try {
          await fetch(config.aplicarResultadoRuletaUrl, {
            method: "POST",
            credentials: "same-origin",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": config.csrfToken,
            },
            body: JSON.stringify({ tokens: 2, resultado: "pregunta_astronauta_lego" }),
          });
        } catch (error) {}
      } else {
        btn.classList.add("incorrecta");

        if (astroFeedback) {
          astroFeedback.className = "astro-lego-feedback visible error";
          astroFeedback.textContent = tLego("lego_astro_feedback_error", "Fallaste. La respuesta correcta era: Trabajo en equipo → Empatía → Creatividad.");
        }
      }

      if (astroClose) astroClose.classList.add("visible");
    });
  });

  astroClose?.addEventListener("click", () => {
    if (!astroOverlay) return;

    astroOverlay.classList.remove("activo");
    astroOverlay.setAttribute("aria-hidden", "true");
    if (astroTrigger) astroTrigger.classList.add("oculto");
  });

  window.addEventListener("idiomaJuegoCambiado", () => {
    if (!astroFeedback || !respondido) return;

    const fueCorrecta = astroFeedback.classList.contains("ok");
    astroFeedback.textContent = fueCorrecta
      ? tLego("lego_astro_feedback_ok", "¡Correcto! La respuesta era Trabajo en equipo → Empatía → Creatividad. Toma tus 2 tokens.")
      : tLego("lego_astro_feedback_error", "Fallaste. La respuesta correcta era: Trabajo en equipo → Empatía → Creatividad.");
  });
}

function inicializarRuletaLego() {
  const config = obtenerConfigLego();

  const modal = document.getElementById("modalRuletaLego");
  const btnAbrir = document.getElementById("btnAbrirRuletaLego");
  const btnCerrar = document.getElementById("btnCerrarRuletaLego");
  const btnLanzar = document.getElementById("btnLanzarRuletaLego");
  const wheel = document.getElementById("ruletaWheel");
  const intentosRestantes = document.getElementById("ruletaIntentosRestantes");
  const intentosTexto = document.getElementById("ruletaIntentosTexto");
  const ultimoResultado = document.getElementById("ruletaUltimoResultado");
  const resultadoActual = document.getElementById("ruletaResultadoActual");
  const storageRuleta = `ruleta_lego_${config.sesionId}_${config.grupoId}`;
  const maxIntentos = 3;
  const opciones = obtenerOpcionesRuleta();

  let girando = false;
  let anguloActual = 0;

  function cargarEstadoRuleta() {
    try {
      const ruleta = JSON.parse(localStorage.getItem(storageRuleta) || "{}");
      return {
        usados: Number(ruleta.usados || 0),
        historial: Array.isArray(ruleta.historial) ? ruleta.historial : [],
      };
    } catch (error) {
      return { usados: 0, historial: [] };
    }
  }

  function guardarEstadoRuleta(data) {
    localStorage.setItem(storageRuleta, JSON.stringify(data));
  }

  function actualizarResumenRuleta() {
    const estado = cargarEstadoRuleta();
    const restantes = Math.max(0, maxIntentos - estado.usados);

    if (intentosRestantes) intentosRestantes.textContent = String(restantes);
    if (intentosTexto) intentosTexto.textContent = `${tLego("lego_ruleta_intentos_disponibles", "Intentos disponibles:")} ${restantes}/${maxIntentos}`;

    const ultimo = estado.historial[estado.historial.length - 1];
    const textoUltimo = ultimo
      ? `${tLego("lego_ruleta_ultimo_resultado", "Último resultado:")} ${ultimo.icono || ""} ${ultimo.titulo} — ${ultimo.detalle}`
      : tLego("lego_ruleta_sin_lanzar", "Aún no has lanzado la ruleta.");

    if (ultimoResultado) ultimoResultado.textContent = textoUltimo;
    if (resultadoActual) resultadoActual.textContent = ultimo
      ? `${ultimo.icono || ""} ${ultimo.titulo}: ${ultimo.detalle}`
      : tLego("lego_ruleta_sin_lanzar", "Aún no has lanzado la ruleta.");

    if (btnLanzar) {
      btnLanzar.disabled = restantes <= 0 || girando || opciones.length === 0;
      btnLanzar.textContent = restantes <= 0
        ? tLego("lego_ruleta_sin_intentos", "Sin intentos")
        : tLego("lego_ruleta_lanzar", "Lanzar ruleta");
    }
  }

  btnAbrir?.addEventListener("click", () => {
    if (!modal) return;

    modal.style.display = "flex";
    actualizarResumenRuleta();
  });

  btnCerrar?.addEventListener("click", () => {
    if (modal) modal.style.display = "none";
  });

  modal?.addEventListener("click", (event) => {
    if (event.target === modal) modal.style.display = "none";
  });

  async function lanzarRuleta() {
    if (girando || opciones.length === 0) return;

    const estado = cargarEstadoRuleta();
    const restantes = maxIntentos - estado.usados;

    if (restantes <= 0) {
      actualizarResumenRuleta();
      return;
    }

    girando = true;

    if (btnLanzar) {
      btnLanzar.disabled = true;
      btnLanzar.textContent = tLego("lego_ruleta_girando", "Girando...");
    }

    const total = opciones.reduce((suma, opcion) => suma + Number(opcion.prob || 0), 0);
    let random = Math.random() * total;
    let opcionElegida = opciones[opciones.length - 1];

    for (const opcion of opciones) {
      random -= Number(opcion.prob || 0);
      if (random <= 0) {
        opcionElegida = opcion;
        break;
      }
    }

    await new Promise((resolve) => {
      if (!wheel) {
        resolve();
        return;
      }

      const audio = document.getElementById("ruletaAudio");
      if (audio) {
        audio.currentTime = 0;
        audio.play().catch(() => {});
      }

      const gradosPorSector = 360 / 8;
      const centro = (Number(opcionElegida.slice || 0) * gradosPorSector) + (gradosPorSector / 2);
      anguloActual += 360 * (5 + Math.floor(Math.random() * 2)) + (360 - centro);
      wheel.style.transform = `rotate(${anguloActual}deg)`;

      setTimeout(resolve, 4200);
    });

    try {
      await fetch(config.aplicarResultadoRuletaUrl, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": config.csrfToken,
        },
        body: JSON.stringify({
          tokens: opcionElegida.tokens,
          resultado: opcionElegida.id,
        }),
      });
    } catch (error) {
      console.error("Error ruleta:", error);
    }

    estado.usados += 1;
    estado.historial.push({
      id: opcionElegida.id,
      titulo: opcionElegida.titulo,
      detalle: opcionElegida.detalle,
      icono: opcionElegida.icono,
      fecha: new Date().toISOString(),
    });

    guardarEstadoRuleta(estado);
    girando = false;
    actualizarResumenRuleta();
  }

  btnLanzar?.addEventListener("click", lanzarRuleta);
  window.addEventListener("idiomaJuegoCambiado", actualizarResumenRuleta);
  actualizarResumenRuleta();
}

function inicializarMusicaLego() {
  const audio = document.getElementById("musica-lego");
  const btn = document.getElementById("btn-musica-lego");

  if (!audio || !btn) return;

  audio.volume = 0.35;

  function arrancar() {
    audio.play().catch(() => {});
    document.removeEventListener("click", arrancar);
    document.removeEventListener("touchstart", arrancar);
  }

  document.addEventListener("click", arrancar);
  document.addEventListener("touchstart", arrancar);

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      audio.pause();
    } else if (!audio.muted) {
      audio.play().catch(() => {});
    }
  });

  btn.addEventListener("click", (event) => {
    event.stopPropagation();
    audio.muted = !audio.muted;
    btn.innerHTML = audio.muted ? "&#128263;" : "&#128266;";
    btn.title = audio.muted ? "Activar música" : "Silenciar música";
    btn.setAttribute("aria-label", audio.muted ? "Activar música" : "Silenciar música");
  });

  window.addEventListener("beforeunload", () => audio.pause());
}

document.addEventListener("DOMContentLoaded", () => {
  inicializarPanelDesafio();
  inicializarIdeasBubblemap();
  inicializarFaseLego();
  inicializarFotoLego();
  inicializarAstroLego();
  inicializarRuletaLego();
  inicializarMusicaLego();
});
