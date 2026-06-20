/* ============================================================
   MINIJUEGO 1 - SOPA DE LETRAS
   ============================================================ */

document.addEventListener("DOMContentLoaded", () => {
  iniciarMusicaSopa();
  iniciarSopaDeLetras();
  iniciarSincronizacionInicioFase();
});

/* ============================================================
   UTILIDADES GENERALES
   ============================================================ */

function tJuego(clave, fallback = "") {
  const idioma = window.i18nJuego?.obtenerIdioma?.() || "es";
  return window.i18nJuego?.traducciones?.[idioma]?.[clave] || fallback;
}

function getCookie(name) {
  let cookieValue = null;

  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");

    for (let cookie of cookies) {
      cookie = cookie.trim();

      if (cookie.substring(0, name.length + 1) === `${name}=`) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }

  return cookieValue;
}

function obtenerRoutes() {
  return document.getElementById("routes");
}

function obtenerSesionId() {
  const routes = obtenerRoutes();

  return (
    routes?.dataset?.sesionId ||
    document.body?.dataset?.sesionId ||
    document.documentElement?.dataset?.sesionId
  );
}

function obtenerGrupoId() {
  const routes = obtenerRoutes();

  return (
    routes?.dataset?.grupoId ||
    document.body?.dataset?.grupoId
  );
}

function obtenerCsrfToken() {
  const routes = obtenerRoutes();

  return (
    routes?.dataset?.csrfToken ||
    document.body?.dataset?.csrfToken ||
    getCookie("csrftoken")
  );
}

/* ============================================================
   MÚSICA DE FONDO
   ============================================================ */

function iniciarMusicaSopa() {
  const audio = document.getElementById("musica-fondo");
  const btn = document.getElementById("btn-musica");

  if (!audio || !btn) return;

  audio.volume = 0.4;

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

  btn.addEventListener("click", () => {
    audio.muted = !audio.muted;
    btn.textContent = audio.muted ? "🔇" : "🔊";
    btn.title = audio.muted ? "Activar música" : "Silenciar música";
    btn.setAttribute("aria-label", btn.title);
  });

  window.musicaSopa = {
    detener: () => {
      audio.pause();
      audio.currentTime = 0;
    },
    reanudar: () => audio.play().catch(() => {}),
  };

  window.addEventListener("beforeunload", () => audio.pause());
}

/* ============================================================
   SONIDO AL ENCONTRAR PALABRA
   ============================================================ */

function prepararSonidoPalabraEncontrada() {
  const AudioCtx = window.AudioContext || window.webkitAudioContext;

  if (!AudioCtx) return;

  let ctx = null;

  function getCtx() {
    if (!ctx) ctx = new AudioCtx();
    if (ctx.state === "suspended") ctx.resume();
    return ctx;
  }

  window.sonarPalabraEncontrada = function () {
    try {
      const c = getCtx();
      const notas = [523.25, 659.25, 783.99];

      notas.forEach((freq, i) => {
        const o = c.createOscillator();
        const g = c.createGain();

        o.connect(g);
        g.connect(c.destination);

        o.type = "sine";
        o.frequency.setValueAtTime(freq, c.currentTime + i * 0.08);

        g.gain.setValueAtTime(0, c.currentTime + i * 0.08);
        g.gain.linearRampToValueAtTime(0.22, c.currentTime + i * 0.08 + 0.02);
        g.gain.exponentialRampToValueAtTime(0.001, c.currentTime + i * 0.08 + 0.25);

        o.start(c.currentTime + i * 0.08);
        o.stop(c.currentTime + i * 0.08 + 0.28);
      });
    } catch (e) {}
  };
}

/* ============================================================
   REGISTRO BACKEND - PALABRAS Y SOPA COMPLETADA
   ============================================================ */

async function registrarPalabraEncontrada(palabra) {
  const routes = obtenerRoutes();
  const url = routes?.dataset?.registrarPalabraUrl;

  if (!url) return;

  try {
    await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": obtenerCsrfToken(),
      },
      credentials: "same-origin",
      body: JSON.stringify({ palabra }),
    });
  } catch (error) {
    console.error("No se pudo registrar palabra:", error);
  }
}

async function registrarSopaCompletada() {
  const routes = obtenerRoutes();
  const url = routes?.dataset?.sopaCompletadaApiUrl;

  if (!url) return { ok: false };

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": obtenerCsrfToken(),
      },
      credentials: "same-origin",
      body: JSON.stringify({}),
    });

    const data = await res.json().catch(() => ({}));

    return {
      ok: res.ok,
      ...data,
    };
  } catch (error) {
    console.error("No se pudo registrar sopa completada:", error);
    return { ok: false };
  }
}

/* ============================================================
   SOPA DE LETRAS - CONFIGURACIÓN
   ============================================================ */

function iniciarSopaDeLetras() {
  prepararSonidoPalabraEncontrada();

  const gridSize = 12;
  const words = [
    "IDEA",
    "EQUIPO",
    "NEGOCIO",
    "CREATIVIDAD",
    "LIDERAZGO",
    "VALOR",
    "IMPACTO",
    "CLIENTE",
  ];

  const gridEl = document.getElementById("grid");
  const statusEl = document.getElementById("status");
  const routesEl = obtenerRoutes();

  if (!gridEl) return;

  document.documentElement.style.setProperty("--cols", gridSize);
  document.documentElement.style.setProperty("--rows", gridSize);

  const DIRS = [
    [1, 0],
    [-1, 0],
    [0, 1],
    [0, -1],
    [1, 1],
    [-1, -1],
    [1, -1],
    [-1, 1],
  ];

  let board = [];
  let mouseDown = false;
  let selection = [];
  let timerInterval = null;
  let gameEnded = false;
  let timerStartedByProfesor = false;
  let ultimaFaseDetectada = null;

  let timeLeft = Number(
    routesEl?.dataset?.tiempoInicial ||
    routesEl?.dataset?.tiempo ||
    document.body?.dataset?.tiempoInicial ||
    300
  );

  if (Number.isNaN(timeLeft) || timeLeft <= 0) {
    timeLeft = 300;
  }

  console.log("Sopa de Letras — build sincronizada • timeLeft =", timeLeft);

  /* ============================================================
     SOPA DE LETRAS - TABLERO
     ============================================================ */

  function createFixedBoard() {
    const gridTemplate = [
      "IDEAUDAXIHHE",
      "DOGZAREDILXC",
      "DAVXRCSNBACL",
      "GHDQTARGWUWI",
      "RNNIEQUIPOHE",
      "OESVVIZAYZFN",
      "WGNKAIIEGYKT",
      "DOCMDLTLLTIE",
      "ZCBXOROADMCR",
      "JIUTLSGREWCB",
      "VOHYJCHDMRIO",
      "IMPACTOULFCL",
    ];

    board = gridTemplate.map((row) => row.split(""));
  }

  function fillRandom() {
    const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";

    for (let r = 0; r < gridSize; r++) {
      for (let c = 0; c < gridSize; c++) {
        if (board[r][c] === "X" || board[r][c] === undefined) {
          board[r][c] = letters[Math.floor(Math.random() * letters.length)];
        }
      }
    }
  }

  function render() {
    gridEl.innerHTML = "";

    for (let r = 0; r < gridSize; r++) {
      for (let c = 0; c < gridSize; c++) {
        const cell = document.createElement("div");

        cell.className = "cell";
        cell.textContent = board[r][c];
        cell.dataset.r = r;
        cell.dataset.c = c;

        cell.addEventListener("mousedown", (e) => {
          e.preventDefault();
          handleDown(e);
        });

        cell.addEventListener("mouseover", (e) => {
          e.preventDefault();
          handleOver(e);
        });

        cell.addEventListener("mouseup", (e) => {
          e.preventDefault();
          handleUp(e);
        });

        cell.addEventListener(
          "touchstart",
          (e) => {
            e.preventDefault();
            handleDown(convertTouch(e));
          },
          { passive: false }
        );

        cell.addEventListener(
          "touchmove",
          (e) => {
            e.preventDefault();
            handleOver(convertTouch(e));
          },
          { passive: false }
        );

        cell.addEventListener(
          "touchend",
          (e) => {
            e.preventDefault();
            handleUp(e);
          },
          { passive: false }
        );

        gridEl.appendChild(cell);
      }
    }

    gridEl.addEventListener("dragstart", (e) => e.preventDefault());
    document.addEventListener("mouseup", cancelDragOutside);
    document.addEventListener("touchend", cancelDragOutside, { passive: false });
  }

  function convertTouch(e) {
    const t = e.touches && e.touches[0]
      ? e.touches[0]
      : e.changedTouches
        ? e.changedTouches[0]
        : null;

    if (!t) return e;

    const el = document.elementFromPoint(t.clientX, t.clientY);

    return {
      currentTarget: el,
      button: 0,
    };
  }

  /* ============================================================
     SOPA DE LETRAS - SELECCIÓN DE CELDAS
     ============================================================ */

  function handleDown(e) {
    if (e.button !== 0) return;
    if (!e.currentTarget || !e.currentTarget.dataset) return;
    if (gameEnded) return;

    mouseDown = true;

    clearTempSelection();
    addToSelection(e.currentTarget);
  }

  function handleOver(e) {
    if (!mouseDown || gameEnded) return;
    if (!e.currentTarget || !e.currentTarget.dataset) return;

    addToSelection(e.currentTarget, true);
  }

  function handleUp() {
    if (!mouseDown) return;

    mouseDown = false;
    checkSelection();
  }

  function cancelDragOutside() {
    if (!mouseDown) return;

    mouseDown = false;
    checkSelection();
  }

  function addToSelection(el, validateLine = false) {
    if (!el || !el.dataset) return;

    const r = parseInt(el.dataset.r, 10);
    const c = parseInt(el.dataset.c, 10);

    if (Number.isNaN(r) || Number.isNaN(c)) return;

    if (selection.some((s) => s.r === r && s.c === c)) return;

    if (validateLine && selection.length >= 1) {
      const r0 = selection[0].r;
      const c0 = selection[0].c;

      const dr = r - r0;
      const dc = c - c0;

      const gcd = (a, b) => (b ? gcd(b, a % b) : Math.abs(a));
      const g = gcd(Math.abs(dr), Math.abs(dc)) || 1;

      const udr = dr / g;
      const udc = dc / g;

      const isValidDir = DIRS.some(([dx, dy]) => dx === udc && dy === udr);

      if (!isValidDir) return;
    }

    el.classList.add("selected");
    selection.push({ r, c, el });
  }

  function clearTempSelection() {
    selection.forEach((s) => s.el && s.el.classList.remove("selected"));
    selection = [];
  }

  function textFromSelection() {
    if (selection.length <= 1) {
      return selection.map((s) => board[s.r][s.c]).join("");
    }

    const s0 = selection[0];
    const s1 = selection[1];

    const dr = Math.sign(s1.r - s0.r);
    const dc = Math.sign(s1.c - s0.c);

    selection.sort((a, b) =>
      (a.r - s0.r) * dr +
      (a.c - s0.c) * dc -
      ((b.r - s0.r) * dr + (b.c - s0.c) * dc)
    );

    return selection.map((s) => board[s.r][s.c]).join("");
  }

  /* ============================================================
     SOPA DE LETRAS - VALIDACIÓN DE PALABRAS
     ============================================================ */

  async function checkSelection() {
    if (selection.length === 0 || gameEnded) return;

    const str = textFromSelection();
    const rev = [...str].reverse().join("");
    const candidates = words.filter((w) => !isWordFound(w));
    const match = candidates.find((w) => w === str || w === rev);

    if (match) {
      selection.forEach((s) => {
        if (!s.el) return;

        s.el.classList.remove("selected");
        s.el.classList.add("found");
        s.el.style.pointerEvents = "none";
      });

      markWordAsFound(match);

      if (typeof window.sonarPalabraEncontrada === "function") {
        window.sonarPalabraEncontrada();
      }

      await registrarPalabraEncontrada(match);

      clearTempSelection();
      updateStatus();

      if (allFound()) {
        endGame(true);
      }
    } else {
      clearTempSelection();
    }
  }

  function getWordListItem(word) {
    let li = document.querySelector(`#word-list li[data-word="${word}"]`);

    if (li) return li;

    const items = document.querySelectorAll("#word-list li");

    for (const item of items) {
      if (item.textContent.trim().toUpperCase() === word) {
        return item;
      }
    }

    return null;
  }

  function isWordFound(word) {
    const li = getWordListItem(word);
    return li ? li.classList.contains("found") : false;
  }

  function markWordAsFound(word) {
    const li = getWordListItem(word);

    if (li) li.classList.add("found");
  }

  function updateStatus() {
    if (!statusEl) return;

    const total = words.length;
    const items = document.querySelectorAll("#word-list li.found");
    const found = items ? items.length : 0;

    statusEl.textContent = `${found}/${total} ${tJuego("sopa_estado_encontradas", "encontradas")}`;
  }

  function allFound() {
    const list = document.querySelectorAll("#word-list li");

    if (!list.length) return false;

    return [...list].every((li) => li.classList.contains("found"));
  }

  /* ============================================================
     SOPA DE LETRAS - FIN DEL JUEGO Y MODALES
     ============================================================ */

  function bloquearJuego() {
    const grid = document.getElementById("grid");

    if (grid) {
      grid.style.pointerEvents = "none";
      grid.style.opacity = "0.4";
    }
  }

  function mostrarEsperandoProfesor() {
    const timerContainer = document.getElementById("timer-container");

    if (timerContainer) {
      timerContainer.classList.remove("blur-target-bloqueado", "timer-esperando");
      timerContainer.classList.add("blur-target-activo");
    }

    const titulo = document.getElementById("tituloSopa");
    const subtitulo = document.getElementById("subtituloSopa");
    const wordsBox = document.getElementById("wordsBox");
    const grid = document.getElementById("grid");

    [titulo, subtitulo, wordsBox, grid].forEach((el) => {
      if (!el) return;

      el.classList.remove("blur-target-activo");
      el.classList.add("blur-target-bloqueado");
    });
  }

  function endGame(won, alarmAudio = null) {
    if (gameEnded) return;

    gameEnded = true;

    bloquearJuego();

    if (typeof window.musicaSopa?.detener === "function") {
      window.musicaSopa.detener();
    }

    if (alarmAudio && !won) {
      try {
        alarmAudio.pause();
        alarmAudio.currentTime = 0;
      } catch (e) {}
    }

    if (!won) {
      pauseTimerLocally();
    }

    if (won) {
      setTimeout(showWinModal, 200);
    } else {
      setTimeout(showTimeUpModal, 0);
    }
  }

  async function showWinModal() {
    if (!gameEnded) return;

    const modal = document.getElementById("winModal");
    const title = document.getElementById("winTitle");
    const esperaEl = document.getElementById("winEspera");

    if (!modal || !title) return;

    const resultado = await registrarSopaCompletada();

    if (resultado?.primer_equipo) {
      title.textContent = tJuego("sopa_win_primer_titulo", "¡Ganaste! Fuiste el primer equipo");
    } else {
      title.textContent = tJuego("sopa_win_otro_titulo", "¡Buen trabajo!");
    }

    if (esperaEl) {
      esperaEl.textContent = tJuego("sopa_win_espera", "Esperando a los demás escuadrones...");
    }

    modal.style.display = "flex";
    modal.setAttribute("aria-hidden", "false");

    const victoryAudio = document.getElementById("victory-sound");

    if (victoryAudio) {
      try {
        victoryAudio.currentTime = 0;
        victoryAudio.play();
      } catch (e) {}
    }
  }

  function showTimeUpModal() {
    if (!gameEnded) return;

    const modal = document.getElementById("timeModal");
    const btn = document.getElementById("btnRetry");

    if (!modal || !btn) return;

    modal.style.display = "flex";
    modal.setAttribute("aria-hidden", "false");

    btn.onclick = () => {
      modal.style.display = "none";
      modal.setAttribute("aria-hidden", "true");

      mostrarEsperandoProfesor();
      revisarEstadoProfesor();
    };
  }

  /* ============================================================
     SOPA DE LETRAS - TIMER
     ============================================================ */

  function renderTimer() {
    const timerEl = document.getElementById("timer");

    if (!timerEl) return;

    const tiempoSeguro = Math.max(0, Number(timeLeft) || 0);
    const min = Math.floor(tiempoSeguro / 60);
    const sec = tiempoSeguro % 60;

    timerEl.textContent = `${min.toString().padStart(2, "0")}:${sec
      .toString()
      .padStart(2, "0")}`;

    if (tiempoSeguro <= 10) {
      timerEl.classList.add("low-time");
    } else {
      timerEl.classList.remove("low-time");
    }
  }

  function pauseTimerLocally() {
    if (timerInterval) {
      clearInterval(timerInterval);
      timerInterval = null;
    }
  }

  function startTimer() {
    const alarmAudio = document.getElementById("alarm-audio");

    if (timerInterval) return;

    renderTimer();

    timerInterval = setInterval(() => {
      timeLeft--;
      renderTimer();

      if (timeLeft <= 0) {
        pauseTimerLocally();
        endGame(false, alarmAudio);
      }
    }, 1000);
  }

  /* ============================================================
     SOPA DE LETRAS - RESPONSIVE GRID
     ============================================================ */

  function ajustarGridResponsive() {
    const root = document.documentElement;
    const cols = gridSize;
    const rows = gridSize;
    const gap = 4;

    const container = document.querySelector(".game-container");
    const wordsBox = document.querySelector(".words");
    const titleEl = document.querySelector("h1");
    const subEl = document.querySelector("p");
    const timerBox = document.getElementById("timer-container");

    if (!container) return;

    const cs = getComputedStyle(container);

    const innerW =
      container.clientWidth -
      parseFloat(cs.paddingLeft) -
      parseFloat(cs.paddingRight);

    const maxWidth = Math.min(innerW, window.innerWidth * 0.94);
    const wordsH = wordsBox ? wordsBox.offsetHeight : 0;

    const headerH =
      (titleEl?.offsetHeight || 0) +
      (subEl?.offsetHeight || 0) +
      (timerBox?.offsetHeight || 0);

    const containerVPadding =
      parseFloat(cs.paddingTop) + parseFloat(cs.paddingBottom);

    const verticalMargins = 40;
    const availableH =
      window.innerHeight - headerH - wordsH - containerVPadding - verticalMargins;

    const cellByWidth = (maxWidth - (cols - 1) * gap - 2 * gap) / cols;
    const cellByHeight = (availableH - (rows - 1) * gap - 2 * gap) / rows;
    const cell = Math.floor(Math.min(cellByWidth, cellByHeight));
    const finalSize = Math.max(22, Math.min(cell, 60));

    root.style.setProperty("--cell-size", `${finalSize}px`);
    root.style.setProperty("--cols", cols);
    root.style.setProperty("--rows", rows);
    root.style.setProperty("--gap", `${gap}px`);
  }

  window.addEventListener("resize", ajustarGridResponsive);

  /* ============================================================
     SOPA DE LETRAS - SINCRONIZACIÓN CON PROFESOR
     ============================================================ */

  function procesarEstadoSesion(data) {
    if (!data) return;

    const faseActual = data.faseActual;
    ultimaFaseDetectada = faseActual;

    if (faseActual && faseActual !== "f1_sopa") {
      if (data.rutaAlumno && window.location.pathname !== data.rutaAlumno) {
        window.location.href = data.rutaAlumno;
      }

      return;
    }

    if (gameEnded) return;

    const backendSeconds = Number(data.segundosRestantes);

    if (!Number.isNaN(backendSeconds) && backendSeconds >= 0) {
      timeLeft = backendSeconds;
      renderTimer();
    }

    if (!timerStartedByProfesor && data.timerCorriendo && data.inicioFaseHabilitado) {
      timerStartedByProfesor = true;
      startTimer();
      return;
    }

    if (timerStartedByProfesor && !data.timerCorriendo) {
      pauseTimerLocally();
      timerStartedByProfesor = false;
    }
  }

  async function revisarEstadoProfesor() {
    try {
      const sesionId = obtenerSesionId();

      if (!sesionId) return;

      const res = await fetch(`/sesion/${sesionId}/estado/`, {
        credentials: "same-origin",
        cache: "no-store",
      });

      if (!res.ok) return;

      const data = await res.json();

      procesarEstadoSesion(data);
    } catch (error) {
      console.error("Error sincronizando sopa:", error);
    }
  }

  window.addEventListener("idiomaJuegoCambiado", () => {
    updateStatus();
  });

  /* ============================================================
     SOPA DE LETRAS - INICIO
     ============================================================ */

  createFixedBoard();
  fillRandom();
  render();
  updateStatus();
  renderTimer();
  ajustarGridResponsive();
  revisarEstadoProfesor();

  setInterval(revisarEstadoProfesor, 1500);
}

/* ============================================================
   INICIO DE FASE - LISTOS + COUNTDOWN
   ============================================================ */

function iniciarSincronizacionInicioFase() {
  const sesionId = obtenerSesionId();
  const grupoId = obtenerGrupoId();
  const csrfToken = obtenerCsrfToken();

  const boton = document.getElementById("btn-listo-fase");
  const textoEspera = document.getElementById("texto-espera-fase");
  const contador = document.getElementById("contador-listos-fase");
  const overlay = document.getElementById("inicio-fase-overlay");

  if (!sesionId || !grupoId || !boton) return;

  let countdownMostrado = false;
  let countdownEnCurso = false;
  let timerRealSolicitado = false;
  let timerLiberadoTrasCountdown = false;

  const blurTargets = [
    document.getElementById("tituloSopa"),
    document.getElementById("subtituloSopa"),
    document.getElementById("timer-container"),
    document.getElementById("grid"),
    document.getElementById("wordsBox"),
  ];

  function textoGruposListos(listos, total) {
    return `${listos}/${total} ${tJuego("sopa_grupos_listos", "grupos listos")}`;
  }

  function textoEsperando() {
    return tJuego("sopa_boton_esperando", "Esperando...");
  }

  function textoListo() {
    return tJuego("sopa_boton_listo", "⚡ Listo para comenzar");
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

    const tc = document.getElementById("timer-container");

    if (tc) tc.classList.add("timer-esperando");
    if (overlay) overlay.classList.remove("overlay-hidden");
  }

  function ejecutarCountdown(callback) {
    if (window.oaiCountdown && typeof window.oaiCountdown.run === "function") {
      window.oaiCountdown.run(callback);
      return;
    }

    callback();
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
        body: JSON.stringify({}),
      });

      const data = await res.json();

      if (!res.ok || !data.ok) {
        throw new Error(data.error || "No se pudo iniciar el timer.");
      }
    } catch (err) {
      console.error("Error iniciando timer sopa:", err);
      timerRealSolicitado = false;
    }
  }

  async function consultarEstado() {
    try {
      const res = await fetch(`/sesion/${sesionId}/estado/`, {
        credentials: "same-origin",
        cache: "no-store",
      });

      if (!res.ok) return;

      const data = await res.json();

      if (contador) {
        contador.textContent = textoGruposListos(
          data.listosInicio || 0,
          data.totalListosInicio || 0
        );
      }

      const miGrupo = (data.grupos || []).find((g) => Number(g.id) === Number(grupoId));

      if (miGrupo && miGrupo.listoF1) {
        boton.disabled = true;
        boton.textContent = textoEsperando();

        if (textoEspera) {
          textoEspera.textContent = tJuego("sopa_esperando", "Esperando a los demás equipos...");
        }
      }

      if (data.faseActual && data.faseActual !== "f1_sopa" && data.rutaAlumno) {
        if (window.location.pathname !== data.rutaAlumno) {
          window.location.href = data.rutaAlumno;
        }

        return;
      }

      if (data.inicioFaseHabilitado) {
        if (countdownMostrado && !countdownEnCurso) {
          activarFase();
        }
      } else {
        countdownMostrado = false;
        countdownEnCurso = false;
        timerRealSolicitado = false;
        timerLiberadoTrasCountdown = false;

        bloquearFase();
      }

      if (data.inicioFaseHabilitado && !countdownMostrado && !countdownEnCurso) {
        countdownEnCurso = true;

        ejecutarCountdown(async () => {
          countdownMostrado = true;
          countdownEnCurso = false;
          timerLiberadoTrasCountdown = true;

          await iniciarTimerRealDespuesCountdown();
          activarFase();
        });
      }
    } catch (err) {
      console.error("Error consultando estado:", err);
    }
  }

  boton.addEventListener("click", async () => {
    boton.disabled = true;
    boton.textContent = textoEsperando();

    try {
      const res = await fetch(`/grupo/${grupoId}/listo/`, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({}),
      });

      const data = await res.json();

      if (!res.ok || !data.ok) {
        throw new Error(data.error || "No se pudo marcar listo.");
      }

      if (contador) {
        contador.textContent = textoGruposListos(data.listos || 0, data.total || 0);
      }

      if (textoEspera) {
        textoEspera.textContent = tJuego("sopa_esperando", "Esperando a los demás equipos...");
      }

      consultarEstado();
    } catch (err) {
      console.error("Error marcando listo:", err);

      boton.disabled = false;
      boton.textContent = textoListo();

      if (textoEspera) {
        textoEspera.textContent = tJuego(
          "sopa_error_listo",
          "No se pudo registrar. Intenta nuevamente."
        );
      }
    }
  });

  window.addEventListener("idiomaJuegoCambiado", () => {
    if (contador) {
      const p = contador.textContent.match(/(\d+)\/(\d+)/);

      if (p) {
        contador.textContent = textoGruposListos(p[1], p[2]);
      }
    }

    if (boton) {
      boton.textContent = boton.disabled ? textoEsperando() : textoListo();
    }

    if (textoEspera) {
      textoEspera.textContent = tJuego("sopa_esperando", "Esperando a los demás equipos...");
    }
  });

  bloquearFase();
  consultarEstado();

  setInterval(consultarEstado, 1500);
}