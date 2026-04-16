const gridSize = 12;
const words = ["IDEA", "EQUIPO", "NEGOCIO", "CREATIVIDAD", "LIDERAZGO"];
const gridEl = document.getElementById("grid");
const statusEl = document.getElementById("status");

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.substring(0, name.length + 1) === (name + "=")) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

async function registrarPalabraEncontrada(palabra) {
  const routes = document.getElementById("routes");
  const url = routes?.dataset?.registrarPalabraUrl;
  if (!url) return;

  try {
    await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken")
      },
      credentials: "same-origin",
      body: JSON.stringify({ palabra })
    });
  } catch (error) {
    console.error("No se pudo registrar palabra:", error);
  }
}

async function registrarSopaCompletada() {
  const routes = document.getElementById("routes");
  const url = routes?.dataset?.sopaCompletadaApiUrl;
  if (!url) return true;

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken")
      },
      credentials: "same-origin",
      body: JSON.stringify({})
    });

    return res.ok;
  } catch (error) {
    console.error("No se pudo registrar sopa completada:", error);
    return false;
  }
}

document.documentElement.style.setProperty("--cols", gridSize);
document.documentElement.style.setProperty("--rows", gridSize);

const DIRS = [
  [1, 0], [-1, 0], [0, 1], [0, -1],
  [1, 1], [-1, -1], [1, -1], [-1, 1]
];

let board = [];
let mouseDown = false;
let selection = [];
let timerInterval = null;
let syncInterval = null;
let gameEnded = false;

const routesEl = document.getElementById("routes");
let timeLeft = Number(
  routesEl?.dataset?.tiempoInicial ||
  routesEl?.dataset?.tiempo ||
  document.body?.dataset?.tiempoInicial ||
  300
);

if (Number.isNaN(timeLeft) || timeLeft <= 0) {
  timeLeft = 300;
}

let timerStartedByProfesor = false;
let ultimaFaseDetectada = null;

console.log("Sopa de Letras — build sincronizada • timeLeft =", timeLeft);

function createFixedBoard() {
  const gridTemplate = [
    "IDEAXXXXXXXX",
    "DXOGZAREDILX",
    "XAXXXXXXXXXX",
    "XXDXXXXXXXXX",
    "XXXIEQUIPOXX",
    "XNXXVXXXXXXX",
    "XEXXXIXXXXXX",
    "XGXXXXTXXXXX",
    "XOXXXXXAXXXX",
    "XCXXXXXXEXXX",
    "XIXXXXXXXRXX",
    "XOXXXXXXXXCX"
  ];
  board = gridTemplate.map(row => row.split(""));
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
  if (!gridEl) return;

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

      cell.addEventListener("touchstart", (e) => {
        e.preventDefault();
        handleDown(convertTouch(e));
      }, { passive: false });

      cell.addEventListener("touchmove", (e) => {
        e.preventDefault();
        handleOver(convertTouch(e));
      }, { passive: false });

      cell.addEventListener("touchend", (e) => {
        e.preventDefault();
        handleUp(e);
      }, { passive: false });

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
    : (e.changedTouches ? e.changedTouches[0] : null);

  if (!t) return e;

  const el = document.elementFromPoint(t.clientX, t.clientY);
  return { currentTarget: el, button: 0 };
}

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
  if (selection.some(s => s.r === r && s.c === c)) return;

  if (validateLine && selection.length >= 1) {
    const r0 = selection[0].r;
    const c0 = selection[0].c;
    const dr = r - r0;
    const dc = c - c0;

    const gcd = (a, b) => b ? gcd(b, a % b) : Math.abs(a);
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
  selection.forEach(s => s.el && s.el.classList.remove("selected"));
  selection = [];
}

function textFromSelection() {
  if (selection.length <= 1) {
    return selection.map(s => board[s.r][s.c]).join("");
  }

  const s0 = selection[0];
  const s1 = selection[1];
  const dr = Math.sign(s1.r - s0.r);
  const dc = Math.sign(s1.c - s0.c);

  selection.sort((a, b) =>
    ((a.r - s0.r) * dr + (a.c - s0.c) * dc) -
    ((b.r - s0.r) * dr + (b.c - s0.c) * dc)
  );

  return selection.map(s => board[s.r][s.c]).join("");
}

function checkSelection() {
  if (selection.length === 0 || gameEnded) return;

  const str = textFromSelection();
  const rev = [...str].reverse().join("");
  const candidates = words.filter(w => !isWordFound(w));
  const match = candidates.find(w => w === str || w === rev);

  if (match) {
    selection.forEach(s => {
      if (!s.el) return;
      s.el.classList.remove("selected");
      s.el.classList.add("found");
      s.el.style.pointerEvents = "none";
    });

    markWordAsFound(match);
    registrarPalabraEncontrada(match);
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
    if (item.textContent.trim().toUpperCase() === word) return item;
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
  statusEl.textContent = `${found}/${total} encontradas`;
}

function allFound() {
  const list = document.querySelectorAll("#word-list li");
  if (!list.length) return false;
  return [...list].every(li => li.classList.contains("found"));
}

function bloquearJuego() {
  const grid = document.getElementById("grid");
  if (grid) {
    grid.style.pointerEvents = "none";
    grid.style.opacity = "0.4";
  }
}

function mostrarEsperandoProfesor() {
  const overlay = document.getElementById("esperandoOverlay");
  if (overlay) {
    overlay.classList.add("visible");
    overlay.setAttribute("aria-hidden", "false");
  }
}

function endGame(won, alarmAudio = null) {
  if (gameEnded) return;

  gameEnded = true;
  bloquearJuego();
  pauseTimerLocally();

  if (alarmAudio && !won) {
    try {
      alarmAudio.pause();
      alarmAudio.currentTime = 0;
    } catch (_) {}
  }

  if (won) {
    setTimeout(showWinModal, 200);
  } else {
    setTimeout(showTimeUpModal, 0);
  }
}

function showWinModal() {
  if (!gameEnded) return;

  const modal = document.getElementById("winModal");
  if (!modal) return;

  modal.style.display = "flex";
  modal.setAttribute("aria-hidden", "false");

  const victoryAudio = document.getElementById("victory-sound");
  if (victoryAudio) {
    try {
      victoryAudio.currentTime = 0;
      victoryAudio.play();
    } catch (_) {}
  }

  setTimeout(() => btn.focus(), 50);
  btn.onclick = goNext;


  setTimeout(() => {
    modal.style.display = "none";
    modal.setAttribute("aria-hidden", "true");
    mostrarEsperandoProfesor();
  }, 4000);
}

function showTimeUpModal() {
  if (!gameEnded) return;

  const modal = document.getElementById("timeModal");
  const btn = document.getElementById("btnRetry");
  if (!modal || !btn) return;

  modal.style.display = "flex";
  modal.setAttribute("aria-hidden", "false");
  btn.onclick = goNext;
}

function renderTimer() {
  const timerEl = document.getElementById("timer");
  if (!timerEl) return;

  const tiempoSeguro = Math.max(0, Number(timeLeft) || 0);
  const min = Math.floor(tiempoSeguro / 60);
  const sec = tiempoSeguro % 60;

  timerEl.textContent = `${min.toString().padStart(2, "0")}:${sec.toString().padStart(2, "0")}`;

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

  if (timerInterval || gameEnded) return;

  renderTimer();

  timerInterval = setInterval(() => {
    if (gameEnded) {
      pauseTimerLocally();
      return;
    }

    timeLeft--;
    renderTimer();

    if (timeLeft <= 0) {
      pauseTimerLocally();
      endGame(false, alarmAudio);
    }
  }, 1000);
}

(function makeGridResponsive() {
  const root = document.documentElement;

  function adjustGrid() {
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
    const innerW = container.clientWidth
      - parseFloat(cs.paddingLeft)
      - parseFloat(cs.paddingRight);

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

    root.style.setProperty("--cell-size", finalSize + "px");
    root.style.setProperty("--cols", cols);
    root.style.setProperty("--rows", rows);
    root.style.setProperty("--gap", gap + "px");
  }

  window.addEventListener("resize", adjustGrid);
  adjustGrid();
})();

function obtenerSesionId() {
  const routes = document.getElementById("routes");
  const sesionId =
    routes?.dataset?.sesionId ||
    document.body?.dataset?.sesionId ||
    document.documentElement?.dataset?.sesionId;

  return sesionId;
}

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

  if ((!timerStartedByProfesor || !data.timerCorriendo) && !Number.isNaN(backendSeconds)) {
    timeLeft = backendSeconds;
    renderTimer();
  }

  if (!timerStartedByProfesor && data.timerCorriendo && data.inicioFaseHabilitado) {
    timerStartedByProfesor = true;

    if (!Number.isNaN(backendSeconds) && backendSeconds >= 0) {
      timeLeft = backendSeconds;
      renderTimer();
    }

    startTimer();
    return;
  }

  if (timerStartedByProfesor && !data.timerCorriendo) {
    pauseTimerLocally();

    if (!Number.isNaN(backendSeconds) && backendSeconds >= 0) {
      timeLeft = backendSeconds;
      renderTimer();
    }

    timerStartedByProfesor = false;
  }
}

async function revisarEstadoProfesor() {
  try {
    const sesionId = obtenerSesionId();
    if (!sesionId) return;

    const res = await fetch(`/sesion/${sesionId}/estado/`, {
      credentials: "same-origin",
      cache: "no-store"
    });

    if (!res.ok) return;

    const data = await res.json();
    procesarEstadoSesion(data);
  } catch (error) {
    console.error("Error sincronizando sopa:", error);
  }
}

(function init() {
  createFixedBoard();
  fillRandom();
  render();
  updateStatus();
  renderTimer();

  revisarEstadoProfesor();
  syncInterval = setInterval(revisarEstadoProfesor, 1500);
})();