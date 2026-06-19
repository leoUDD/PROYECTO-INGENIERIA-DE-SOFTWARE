document.addEventListener("DOMContentLoaded", () => {
  inicializarAudioGlobal();
  inicializarDialogoRPG();
  inicializarConocidos();
});

function tJuego(clave, fallback = "") {
  const idioma = window.i18nJuego?.obtenerIdioma?.() || "es";
  return window.i18nJuego?.traducciones?.[idioma]?.[clave] || fallback;
}

function textoGruposListos(listos, total) {
  return `${listos}/${total} ${tJuego("conocidos_grupos_listos", "grupos listos")}`;
}

function textoEsperando() {
  return tJuego("conocidos_boton_esperando", "Esperando...");
}

function textoListoComenzar() {
  return tJuego("conocidos_boton_listo", "⚡ Listo para comenzar");
}

/* ============================================================
   AUDIO GENERAL
   ============================================================ */

function inicializarAudioGlobal() {
  const AudioCtx = window.AudioContext || window.webkitAudioContext;

  if (!AudioCtx) return;

  let ctx = null;

  function getCtx() {
    if (!ctx) ctx = new AudioCtx();
    if (ctx.state === "suspended") ctx.resume();
    return ctx;
  }

  window.sonarTecla = function () {
    try {
      const c = getCtx();
      const o = c.createOscillator();
      const g = c.createGain();

      o.connect(g);
      g.connect(c.destination);

      o.type = "square";
      o.frequency.setValueAtTime(520, c.currentTime);
      o.frequency.exponentialRampToValueAtTime(380, c.currentTime + 0.04);

      g.gain.setValueAtTime(0.05, c.currentTime);
      g.gain.exponentialRampToValueAtTime(0.001, c.currentTime + 0.05);

      o.start(c.currentTime);
      o.stop(c.currentTime + 0.06);
    } catch (e) {}
  };

  window.sonarBoton = function () {
    try {
      const c = getCtx();

      [
        [440, 600, 0, 0.08, 0.18, 0.14],
        [660, 880, 0.06, 0.18, 0.12, 0.22],
      ].forEach(([f1, f2, delay, ramp, vol, stop]) => {
        const o = c.createOscillator();
        const g = c.createGain();

        o.connect(g);
        g.connect(c.destination);

        o.type = "sine";
        o.frequency.setValueAtTime(f1, c.currentTime + delay);
        o.frequency.exponentialRampToValueAtTime(f2, c.currentTime + delay + ramp);

        g.gain.setValueAtTime(vol, c.currentTime + delay);
        g.gain.exponentialRampToValueAtTime(0.001, c.currentTime + delay + stop);

        o.start(c.currentTime + delay);
        o.stop(c.currentTime + delay + stop + 0.02);
      });
    } catch (e) {}
  };
}

/* ============================================================
   DIÁLOGO RPG
   ============================================================ */

function inicializarDialogoRPG() {
  const GUION = [
    { texto: "¡Hola, Agentes! Soy la Comandante Nova, su guía en esta misión." },
    { texto: "Están a punto de comenzar una experiencia que pondrá a prueba su escuadrón." },
    { texto: "¿Están listos para aceptar el desafío?" },
  ];

  let paso = 0;
  let escribiendo = false;
  let textoCompleto = "";
  let timerEscritura = null;
  let teclaCounter = 0;

  const overlayDialogo = document.getElementById("dialogo-inicial-overlay");
  const burbuja = document.getElementById("dialogo-burbuja");
  const textoEl = document.getElementById("dialogo-texto");
  const btnLabel = document.getElementById("btn-rpg-label");
  const dotsEl = document.getElementById("dialogo-dots");
  const btnContinuar = document.getElementById("btn-dialogo-continuar");

  if (!overlayDialogo || !burbuja || !textoEl || !btnLabel || !dotsEl || !btnContinuar) return;

  GUION.forEach((_, i) => {
    const d = document.createElement("div");
    d.className = "d-dot";
    d.id = `dot-${i}`;
    dotsEl.appendChild(d);
  });

  function actualizarDots() {
    GUION.forEach((_, i) => {
      const d = document.getElementById(`dot-${i}`);
      d.className = `d-dot${i < paso ? " hecho" : i === paso ? " activo" : ""}`;
    });
  }

  function escribirTexto(txt) {
    textoCompleto = txt;
    escribiendo = true;
    textoEl.innerHTML = "";
    teclaCounter = 0;

    const cursor = document.createElement("span");
    cursor.className = "cursor-rpg";

    let i = 0;

    clearInterval(timerEscritura);

    timerEscritura = setInterval(() => {
      if (i < txt.length) {
        textoEl.textContent = txt.slice(0, i + 1);
        textoEl.appendChild(cursor);
        teclaCounter++;

        if (
          teclaCounter % 2 === 0 &&
          txt[i] !== " " &&
          typeof window.sonarTecla === "function"
        ) {
          window.sonarTecla();
        }

        i++;
      } else {
        clearInterval(timerEscritura);
        escribiendo = false;
        textoEl.textContent = txt;
      }
    }, 30);
  }

  function mostrarPaso(n) {
    actualizarDots();
    btnLabel.textContent = n === GUION.length - 1 ? "¡Listos!" : "Siguiente";
    escribirTexto(GUION[n].texto);
  }

  window.dialogoSiguiente = function () {
    if (typeof window.sonarBoton === "function") window.sonarBoton();

    if (escribiendo) {
      clearInterval(timerEscritura);
      escribiendo = false;
      textoEl.textContent = textoCompleto;
      return;
    }

    paso++;

    if (paso >= GUION.length) {
      overlayDialogo.classList.remove("visible");
      overlayDialogo.classList.add("oculto");
      return;
    }

    mostrarPaso(paso);
  };

  btnContinuar.addEventListener("click", window.dialogoSiguiente);

  window._mostrarDialogoNova = function () {
    overlayDialogo.classList.remove("oculto");
    overlayDialogo.classList.add("visible");

    setTimeout(() => {
      burbuja.classList.add("visible");
      mostrarPaso(0);
    }, 200);
  };
}

/* ============================================================
   LÓGICA PRINCIPAL
   ============================================================ */

function inicializarConocidos() {
  const musicaFondo = document.getElementById("musica-fondo");

  if (musicaFondo) {
    musicaFondo.volume = 0.4;

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

  const routesEl = document.getElementById("routes");

  const sesionId = routesEl?.dataset?.sesionId;
  const grupoId = routesEl?.dataset?.grupoId;
  const csrfToken = routesEl?.dataset?.csrfToken;

  const timerElement = document.getElementById("timer");
  const alarmAudio = document.getElementById("alarm-audio");
  const btnPregunta = document.getElementById("btnPregunta");
  const preguntaTexto = document.getElementById("preguntaTexto");
  const overlay = document.getElementById("inicio-fase-overlay");
  const botonListo = document.getElementById("btn-listo-fase");
  const textoEspera = document.getElementById("texto-espera-fase");
  const contadorListos = document.getElementById("contador-listos-fase");
  const astroTrigger = document.getElementById("astro-trigger");
  const astroOverlay = document.getElementById("astro-overlay");
  const astroClose = document.getElementById("astro-close");

  const blurTargets = [
    document.getElementById("tituloConocidos"),
    document.getElementById("speechBubbleConocidos"),
    document.getElementById("timer"),
  ];

  const preguntas = [
    "conocidos_pregunta_1",
    "conocidos_pregunta_2",
    "conocidos_pregunta_3",
    "conocidos_pregunta_4",
    "conocidos_pregunta_5",
    "conocidos_pregunta_6",
    "conocidos_pregunta_7",
    "conocidos_pregunta_8",
    "conocidos_pregunta_9",
    "conocidos_pregunta_10",
  ];

  let ultimoIndice = -1;
  let timeLeft = Number(routesEl?.dataset?.tiempo || 10);
  let timerInterval = null;
  let timerIniciado = false;
  let redirigiendo = false;
  let yaListo = false;
  let astroActivo = false;
  let astroCerrado = false;
  let yaDialogoMostrado = false;

  let countdownMostrado = false;
  let countdownEnCurso = false;
  let timerRealSolicitado = false;
  let timerLiberadoTrasCountdown = false;
  let tiempoFinalizado = false;

  function cambiarPregunta() {
    if (!preguntaTexto) return;

    let random = Math.floor(Math.random() * preguntas.length);

    if (preguntas.length > 1) {
      while (random === ultimoIndice) {
        random = Math.floor(Math.random() * preguntas.length);
      }
    }

    ultimoIndice = random;
    preguntaTexto.textContent = `👉 ${tJuego(preguntas[random], preguntas[random])}`;
  }

  function pintarTiempo() {
    if (!timerElement) return;

    const minutes = Math.floor(Math.max(0, timeLeft) / 60);
    const seconds = Math.max(0, timeLeft) % 60;

    timerElement.textContent = `${minutes.toString().padStart(2, "0")}:${seconds
      .toString()
      .padStart(2, "0")}`;
  }

  function reproducirAlarma() {
    if (!alarmAudio) return;

    alarmAudio.currentTime = 0;
    alarmAudio.play().catch(() => {});

    document.body.classList.add("flash");

    setTimeout(() => {
      document.body.classList.remove("flash");
    }, 800);
  }

  function pausarTimerLocal() {
    if (timerInterval) {
      clearInterval(timerInterval);
      timerInterval = null;
    }
  }

  function iniciarTimerLocal() {
    if (timerInterval || redirigiendo) return;

    timerIniciado = true;
    pintarTiempo();

    timerInterval = setInterval(() => {
      if (redirigiendo) {
        pausarTimerLocal();
        return;
      }

      if (timeLeft > 0) {
        timeLeft--;
        pintarTiempo();
      }

      if (timeLeft <= 0) {
        timeLeft = 0;
        pintarTiempo();
        pausarTimerLocal();

        if (!tiempoFinalizado) {
          tiempoFinalizado = true;
          reproducirAlarma();
        }
      }
    }, 1000);
  }

  async function iniciarTimerRealDespuesCountdown() {
    if (timerRealSolicitado) return;

    timerRealSolicitado = true;

    try {
      const res = await fetch(`/sesion/${sesionId}/iniciar-timer-inicio-fase/`, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({ fase: "f1_conocidos" }),
      });

      const data = await res.json();

      if (!res.ok || !data.ok) {
        throw new Error(data.error || "No se pudo iniciar el timer.");
      }

      const backendSeconds = Number(data.segundosRestantes);

      if (!Number.isNaN(backendSeconds)) {
        timeLeft = backendSeconds;
        pintarTiempo();
      }
    } catch (err) {
      console.error("Error iniciando timer conocidos:", err);
      timerRealSolicitado = false;
    }
  }

  function activarFase() {
    blurTargets.forEach((el) => {
      if (!el) return;

      el.classList.remove("blur-target-bloqueado", "timer-esperando");
      el.classList.add("blur-target-activo");
    });

    if (overlay) overlay.classList.add("overlay-hidden");

    if (!yaDialogoMostrado && typeof window._mostrarDialogoNova === "function") {
      yaDialogoMostrado = true;
      window._mostrarDialogoNova();
    }
  }

  function bloquearFase() {
    blurTargets.forEach((el) => {
      if (!el) return;

      el.classList.remove("blur-target-activo");
      el.classList.add("blur-target-bloqueado");
    });

    if (timerElement) timerElement.classList.add("timer-esperando");
    if (overlay) overlay.classList.remove("overlay-hidden");
  }

  function sincronizarBoton(miGrupo) {
    if (!botonListo) return;

    if (miGrupo && miGrupo.listoLobby) {
      yaListo = true;
      botonListo.disabled = true;
      botonListo.textContent = textoEsperando();

      if (textoEspera) {
        textoEspera.textContent = tJuego(
          "conocidos_esperando",
          "Esperando a los demás equipos..."
        );
      }
    }
  }

  function ejecutarCountdown(callback) {
    if (window.oaiCountdown && typeof window.oaiCountdown.run === "function") {
      window.oaiCountdown.run(callback);
      return;
    }

    callback();
  }

  function procesarEstadoSesion(data) {
    if (!data) return;

    if (contadorListos) {
      contadorListos.textContent = textoGruposListos(
        data.gruposListosLobby || 0,
        data.totalGrupos || 0
      );
    }

    const miGrupo = (data.grupos || []).find((g) => Number(g.id) === Number(grupoId)) || null;

    sincronizarBoton(miGrupo);

    if (data.faseActual && data.faseActual !== "f1_conocidos") {
      if (data.rutaAlumno && window.location.pathname !== data.rutaAlumno) {
        redirigiendo = true;
        window.location.href = data.rutaAlumno;
      }

      return;
    }

    if (data.inicioFaseHabilitado) {
      if (countdownMostrado && !countdownEnCurso) activarFase();
    } else {
      countdownMostrado = false;
      countdownEnCurso = false;
      timerLiberadoTrasCountdown = false;
      timerRealSolicitado = false;
      bloquearFase();
    }

    const backendSeconds = Number(data.segundosRestantes);

    if ((!timerIniciado || !data.timerCorriendo) && !Number.isNaN(backendSeconds)) {
      if (!countdownEnCurso && !timerLiberadoTrasCountdown && !tiempoFinalizado) {
        timeLeft = backendSeconds;
        pintarTiempo();
      }
    }

    if (data.inicioFaseHabilitado && backendSeconds <= 0 && !data.timerCorriendo) {
      if (!tiempoFinalizado) {
        tiempoFinalizado = true;
        reproducirAlarma();
      }

      return;
    }

    if (!timerIniciado && data.inicioFaseHabilitado) {
      if (!countdownMostrado && !countdownEnCurso) {
        countdownEnCurso = true;

        ejecutarCountdown(async () => {
          countdownMostrado = true;
          countdownEnCurso = false;
          timerLiberadoTrasCountdown = true;

          await iniciarTimerRealDespuesCountdown();
          activarFase();
        });

        return;
      }

      if (!countdownMostrado || countdownEnCurso || !timerLiberadoTrasCountdown) return;
      if (!data.timerCorriendo) return;

      if (!Number.isNaN(backendSeconds)) {
        timeLeft = backendSeconds;
        pintarTiempo();
      }

      timerIniciado = true;
      iniciarTimerLocal();
      return;
    }

    if (timerIniciado && !data.timerCorriendo && !tiempoFinalizado) {
      pausarTimerLocal();

      if (!Number.isNaN(backendSeconds)) {
        timeLeft = backendSeconds;
        pintarTiempo();
      }

      timerIniciado = false;
    }
  }

  async function consultarEstadoSesion() {
    if (redirigiendo || !sesionId) return;

    try {
      const res = await fetch(`/sesion/${sesionId}/estado/`, {
        cache: "no-store",
        credentials: "same-origin",
      });

      if (!res.ok) return;

      const data = await res.json();

      procesarEstadoSesion(data);
    } catch (err) {
      console.error("Error consultando estado:", err);
    }
  }

  function abrirAstro() {
    if (astroActivo || astroCerrado || !astroTrigger || !astroOverlay) return;

    astroActivo = true;
    astroTrigger.classList.add("oculto");
    astroOverlay.classList.add("activo");
    astroOverlay.setAttribute("aria-hidden", "false");
  }

  function cerrarAstro() {
    if (!astroActivo || !astroOverlay) return;

    astroOverlay.classList.remove("activo");
    astroOverlay.setAttribute("aria-hidden", "true");

    astroActivo = false;
    astroCerrado = true;
  }

  if (btnPregunta) {
    btnPregunta.addEventListener("click", cambiarPregunta);
    cambiarPregunta();
  }

  if (astroTrigger) {
    astroTrigger.addEventListener("click", abrirAstro);
  }

  if (astroClose) {
    astroClose.addEventListener("click", cerrarAstro);
  }

  if (botonListo) {
    botonListo.addEventListener("click", async () => {
      if (yaListo) return;

      botonListo.disabled = true;
      botonListo.textContent = textoEsperando();

      try {
        const res = await fetch(`/grupo/${grupoId}/listo/`, {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
          },
          body: JSON.stringify({ fase: "f1_conocidos" }),
        });

        const data = await res.json();

        yaListo = true;

        if (contadorListos) {
          contadorListos.textContent = textoGruposListos(data.listos || 0, data.total || 0);
        }

        if (textoEspera) {
          textoEspera.textContent = tJuego(
            "conocidos_esperando",
            "Esperando a los demás equipos..."
          );
        }

        if (data.inicio_fase_habilitado) {
          consultarEstadoSesion();
        }
      } catch (err) {
        console.error("Error marcando listo:", err);

        botonListo.disabled = false;
        botonListo.textContent = textoListoComenzar();
        yaListo = false;
      }
    });
  }

  window.addEventListener("idiomaJuegoCambiado", () => {
    if (ultimoIndice >= 0 && preguntaTexto) {
      preguntaTexto.textContent = `👉 ${tJuego(preguntas[ultimoIndice], preguntas[ultimoIndice])}`;
    }

    if (contadorListos) {
      const p = contadorListos.textContent.match(/(\d+)\/(\d+)/);

      if (p) {
        contadorListos.textContent = textoGruposListos(p[1], p[2]);
      }
    }

    if (botonListo) {
      botonListo.textContent = botonListo.disabled ? textoEsperando() : textoListoComenzar();
    }

    if (textoEspera) {
      textoEspera.textContent = tJuego(
        "conocidos_esperando",
        "Esperando a los demás equipos..."
      );
    }
  });

  bloquearFase();
  pintarTiempo();

  setInterval(consultarEstadoSesion, 1500);
  consultarEstadoSesion();
}