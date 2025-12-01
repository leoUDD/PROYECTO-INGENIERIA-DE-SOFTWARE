// === CONFIGURACIÓN (fija) ===
const gridSize = 12;
const words = ["IDEA", "EQUIPO", "NEGOCIO", "CREATIVIDAD", "LIDERAZGO"];
const gridEl = document.getElementById("grid");
const statusEl = document.getElementById("status");

// Sincroniza columnas/filas en CSS
document.documentElement.style.setProperty('--cols', gridSize);
document.documentElement.style.setProperty('--rows', gridSize);

// Direcciones permitidas (líneas rectas)
const DIRS = [
  [1, 0], [-1, 0], [0, 1], [0, -1],
  [1, 1], [-1, -1], [1, -1], [-1, 1]
];

let board = [];
let mouseDown = false;
let selection = [];

// === ESTADO GLOBAL ===
let timerInterval = null;
let gameEnded = false;
let timeLeft = 45; // segundos

console.log("Sopa de Letras — JS v10 — timeLeft =", timeLeft);

/* ============================================================
   TABLERO FIJO + LETRAS RANDOM
   ============================================================ */
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

/* ============================================================
   RENDERIZADO
   ============================================================ */
function render() {
  gridEl.innerHTML = "";
  for (let r = 0; r < gridSize; r++) {
    for (let c = 0; c < gridSize; c++) {

      const cell = document.createElement("div");
      cell.className = "cell";
      cell.textContent = board[r][c];
      cell.dataset.r = r;
      cell.dataset.c = c;

      // Eventos mouse
      cell.addEventListener("mousedown", (e) => { e.preventDefault(); handleDown(e); });
      cell.addEventListener("mouseover", (e) => { e.preventDefault(); handleOver(e); });
      cell.addEventListener("mouseup",     (e) => { e.preventDefault(); handleUp(); });

      // Eventos tactiles
      cell.addEventListener("touchstart", (e) => { e.preventDefault(); handleDown(convertTouch(e)); }, { passive:false });
      cell.addEventListener("touchmove",  (e) => { e.preventDefault(); handleOver(convertTouch(e)); }, { passive:false });
      cell.addEventListener("touchend",   (e) => { e.preventDefault(); handleUp(); }, { passive:false });

      gridEl.appendChild(cell);
    }
  }

  gridEl.addEventListener('dragstart', e => e.preventDefault());
  document.addEventListener("mouseup", cancelDragOutside);
  document.addEventListener("touchend", cancelDragOutside, { passive:false });
}

function convertTouch(e){
  const t = e.touches?.[0] || e.changedTouches?.[0];
  if (!t) return e;
  const el = document.elementFromPoint(t.clientX, t.clientY);
  return { currentTarget: el, button: 0 };
}

/* ============================================================
   MANEJO DE SELECCIÓN
   ============================================================ */
function handleDown(e) {
  if (e.button !== 0 || gameEnded) return;
  if (!e.currentTarget.dataset) return;
  mouseDown = true;
  clearTempSelection();
  addToSelection(e.currentTarget);
}

function handleOver(e) {
  if (!mouseDown || gameEnded) return;
  if (!e.currentTarget.dataset) return;
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
  const r = parseInt(el.dataset.r);
  const c = parseInt(el.dataset.c);

  if (selection.some(s => s.r === r && s.c === c)) return;

  // Validar línea recta
  if (validateLine && selection.length >= 1) {
    const r0 = selection[0].r, c0 = selection[0].c;
    const dr = r - r0, dc = c - c0;
    const gcd = (a, b) => b ? gcd(b, a % b) : Math.abs(a);
    const g = gcd(Math.abs(dr), Math.abs(dc)) || 1;
    const udr = dr / g, udc = dc / g;
    const isValid = DIRS.some(([dx, dy]) => dx === udc && dy === udr);
    if (!isValid) return;
  }

  el.classList.add("selected");
  selection.push({ r, c, el });
}

function clearTempSelection() {
  selection.forEach(s => s.el.classList.remove("selected"));
  selection = [];
}

function textFromSelection() {
  if (selection.length <= 1)
    return selection.map(s => board[s.r][s.c]).join("");

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
      s.el.classList.remove("selected");
      s.el.classList.add("found");
      s.el.style.pointerEvents = "none";
    });

    markWordAsFound(match);
    clearTempSelection();
    updateStatus();

    if (allFound()) {
      endGame(true);
    }

  } else {
    clearTempSelection();
  }
}

/* ============================================================
   LISTA DE PALABRAS
   ============================================================ */
function getWordListItem(word){
  const items = document.querySelectorAll("#word-list li");
  for (const li of items){
    if (li.textContent.trim().toUpperCase() === word)
      return li;
  }
  return null;
}
function isWordFound(word){
  const li = getWordListItem(word);
  return li?.classList.contains("found");
}
function markWordAsFound(word){
  const li = getWordListItem(word);
  if (li) li.classList.add("found");
}
function allFound(){
  return [...document.querySelectorAll("#word-list li")]
    .every(li => li.classList.contains("found"));
}
function updateStatus(){
  const total = words.length;
  const found = document.querySelectorAll('#word-list li.found').length;
  statusEl.textContent = `${found}/${total} encontradas`;
}

/* ============================================================
   CIERRE DEL JUEGO
   ============================================================ */
function endGame(won){
  if (gameEnded) return;
  gameEnded = true;
  clearInterval(timerInterval);

  if (won){
    showWinModal();
  } else {
    const alarm = document.getElementById("alarm-audio");
    if (alarm){
      alarm.currentTime = 0;
      alarm.play();
    }
    showTimeUpModal();
  }
}

/* ============================================================
   MODALES
   ============================================================ */
function showWinModal(){
  const modal = document.getElementById("winModal");
  const btn = document.getElementById("btnNext");
  const audio = document.getElementById("victory-sound");

  modal.style.display = "flex";
  modal.setAttribute("aria-hidden","false");

  if (audio){
    audio.currentTime = 0;
    audio.play();
  }
  btn.addEventListener("click", goNext, { once:true });
}

function showTimeUpModal(){
  const modal = document.getElementById("timeModal");
  const btn = document.getElementById("btnRetry");

  modal.style.display = "flex";
  modal.setAttribute("aria-hidden","false");

  btn.addEventListener("click", goNext, { once:true });
}

function goNext(){
  const url = document.getElementById("routes").dataset.tematicasUrl;
  if (url) window.location.href = url;
}

/* ============================================================
   TEMPORIZADOR
   ============================================================ */
function startTimer(){
  const timerEl = document.getElementById("timer");
  const alarm = document.getElementById("alarm-audio");

  function tick(){
    if (gameEnded){
      clearInterval(timerInterval);
      return;
    }

    const min = Math.floor(timeLeft / 60);
    const sec = timeLeft % 60;
    timerEl.textContent = `${min.toString().padStart(2,'0')}:${sec.toString().padStart(2,'0')}`;

    if (timeLeft <= 10)
      timerEl.classList.add("low-time");

    if (timeLeft <= 0){
      clearInterval(timerInterval);
      endGame(false);
      return;
    }

    timeLeft--;
  }

  timerInterval = setInterval(tick, 1000);
  tick();
}

/* ============================================================
   GRILLA RESPONSIVA
   ============================================================ */
(function makeGridResponsive(){
  const root = document.documentElement;

  function adjust(){
    const cols = gridSize;
    const rows = gridSize;
    const gap = 4;

    const container = document.querySelector(".game-container");
    const wordsBox  = document.querySelector(".words");
    const titleEl   = document.querySelector("h1");
    const subEl     = document.querySelector("p");
    const timerBox  = document.getElementById("timer-container");

    const cs = getComputedStyle(container);
    const innerW = container.clientWidth
                 - parseFloat(cs.paddingLeft)
                 - parseFloat(cs.paddingRight);

    const maxWidth = Math.min(innerW, window.innerWidth * 0.94);

    const wordsH = wordsBox.offsetHeight;
    const headerH = (titleEl?.offsetHeight || 0)
                  + (subEl?.offsetHeight || 0)
                  + (timerBox?.offsetHeight || 0);

    const containerVPadding = parseFloat(cs.paddingTop) + parseFloat(cs.paddingBottom);
    const availableH = window.innerHeight - headerH - wordsH - containerVPadding - 40;

    const cellByWidth  = (maxWidth  - (cols - 1) * gap - 2 * gap) / cols;
    const cellByHeight = (availableH - (rows - 1) * gap - 2 * gap) / rows;

    const cell = Math.floor(Math.min(cellByWidth, cellByHeight));
    const finalSize = Math.max(22, Math.min(cell, 60));

    root.style.setProperty("--cell-size", finalSize + "px");
    root.style.setProperty("--gap", gap + "px");
  }

  window.addEventListener("resize", adjust);
  adjust();
})();

/* ============================================================
   INICIO
   ============================================================ */
(function init(){
  createFixedBoard();
  fillRandom();
  render();
  updateStatus();
  startTimer();
})();

