const gridSize = 12;
const words = ["IDEA", "EQUIPO", "NEGOCIO", "CREATIVIDAD", "LIDERAZGO"];
const gridEl = document.getElementById("grid");
const statusEl = document.getElementById("status");

document.documentElement.style.setProperty('--cols', gridSize);
document.documentElement.style.setProperty('--rows', gridSize);

// 8 direcciones: horizontales, verticales y diagonales
const DIRS = [
  [1, 0],  [-1, 0],  [0, 1],  [0, -1],
  [1, 1],  [-1, -1], [1, -1], [-1, 1]
];

let board = [];
let mouseDown = false;
let selection = [];
let timerInterval = null;
let gameEnded = false;
let timeLeft = 45;

console.log("Sopa de Letras — build v3 • timeLeft =", timeLeft);

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
  gridEl.innerHTML = "";
  for (let r = 0; r < gridSize; r++) {
    for (let c = 0; c < gridSize; c++) {
      const cell = document.createElement("div");
      cell.className = "cell";
      cell.textContent = board[r][c];
      cell.dataset.r = r;
      cell.dataset.c = c;

      // Evita selección azul y gestos por defecto
      cell.addEventListener("mousedown", (e)=>{ e.preventDefault(); handleDown(e); });
      cell.addEventListener("mouseover", (e)=>{ e.preventDefault(); handleOver(e); });
      cell.addEventListener("mouseup",   (e)=>{ e.preventDefault(); handleUp(e); });

      // Soporte táctil básico
      cell.addEventListener("touchstart", (e)=>{ e.preventDefault(); handleDown(convertTouch(e)); }, {passive:false});
      cell.addEventListener("touchmove",  (e)=>{ e.preventDefault(); handleOver(convertTouch(e)); }, {passive:false});
      cell.addEventListener("touchend",   (e)=>{ e.preventDefault(); handleUp(); }, {passive:false});

      gridEl.appendChild(cell);
    }
  }

  gridEl.addEventListener('dragstart', (e)=> e.preventDefault());
  document.addEventListener("mouseup", cancelDragOutside);
  document.addEventListener("touchend", cancelDragOutside, {passive:false});
}

function convertTouch(e){
  const t = e.touches && e.touches[0] ? e.touches[0] : (e.changedTouches ? e.changedTouches[0] : null);
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
    const r0 = selection[0].r, c0 = selection[0].c;
    const dr = r - r0, dc = c - c0;
    const gcd = (a, b) => b ? gcd(b, a % b) : Math.abs(a);
    const g = gcd(Math.abs(dr), Math.abs(dc)) || 1;
    const udr = dr / g, udc = dc / g;
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
  if (selection.length <= 1) return selection.map(s => board[s.r][s.c]).join("");
  const s0 = selection[0];
  const s1 = selection[1];
  const dr = Math.sign(s1.r - s0.r);
  const dc = Math.sign(s1.c - s0.c);
  selection.sort((a, b) =>
    ((a.r - s0.r) * dr + (a.c - s0.c) * dc) - ((b.r - s0.r) * dr + (b.c - s0.c) * dc)
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
    clearTempSelection();
    updateStatus();

    if (allFound()) {
      endGame(true);
      return;
    }
  } else {
    clearTempSelection();
  }
}

// ===== Utilidades para la lista =====
function getWordListItem(word) {
  let li = document.querySelector(`#word-list li[data-word="${word}"]`);
  if (li) return li;
  const items = document.querySelectorAll('#word-list li');
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
  const items = document.querySelectorAll('#word-list li.found');
  const found = items ? items.length : 0;
  statusEl.textContent = `${found}/${total} encontradas`;
}

function allFound() {
  const list = document.querySelectorAll('#word-list li');
  if (!list.length) return false;
  return [...list].every(li => li.classList.contains("found"));
}

/* ===== Cierre unificado del juego ===== */
function endGame(won, alarmAudio = null) {
  if (gameEnded) return;
  gameEnded = true;
  clearInterval(timerInterval);

  // si venía de tiempo agotado y estaba sonando la alarma
  if (alarmAudio && !won) {
    try { alarmAudio.pause(); alarmAudio.currentTime = 0; } catch(_) {}
  }

  if (won) {
    setTimeout(showWinModal, 200);
  } else {
    setTimeout(showTimeUpModal, 0);
  }
}

/* ===== Modales ===== */
function showWinModal(){
  if (!gameEnded) return;
  const modal = document.getElementById('winModal');
  const btn = document.getElementById('btnNext');
  if (!modal || !btn) return;

  modal.style.display = 'flex';
  modal.setAttribute('aria-hidden', 'false');

  const victoryAudio = document.getElementById('victory-sound');
  if (victoryAudio){ victoryAudio.currentTime = 0; victoryAudio.play(); }

  setTimeout(() => btn.focus(), 50);
  btn.addEventListener('click', goNext, { once: true });
}

function goNext(){
  const routes = document.getElementById('routes');
  const url = routes?.dataset.sopaCompletadaUrl;
  if (url) window.location.href = url;
}

function showTimeUpModal() {
  if (!gameEnded) return;
  const modal = document.getElementById('timeModal');
  const btn = document.getElementById('btnRetry');
  if (!modal || !btn) return;

  modal.style.display = 'flex';
  modal.setAttribute('aria-hidden', 'false');
  btn.addEventListener('click', goNext, { once: true });
}

/* ===== Temporizador (45s) ===== */
function startTimer() {
  const timerEl = document.getElementById('timer');
  const alarmAudio = document.getElementById('alarm-audio');

  function updateTimer() {
    if (gameEnded) {
      clearInterval(timerInterval);
      return;
    }

    const min = Math.floor(timeLeft / 60);
    const sec = timeLeft % 60;
    timerEl.textContent = `${min.toString().padStart(2,'0')}:${sec.toString().padStart(2,'0')}`;

    if (timeLeft <= 10) timerEl.classList.add('low-time');

    if (timeLeft <= 0) {
      clearInterval(timerInterval);
      endGame(false, alarmAudio);
      return;
    }
    timeLeft--;
  }

  timerInterval = setInterval(updateTimer, 1000);
  updateTimer();
}

/* ===== Ajuste de grilla 100% responsiva ===== */
(function makeGridResponsive(){
  const root = document.documentElement;

  function adjustGrid(){
    const cols = gridSize;
    const rows = gridSize;
    const gap = 4;

    const container = document.querySelector('.game-container');
    const wordsBox  = document.querySelector('.words');
    const titleEl   = document.querySelector('h1');
    const subEl     = document.querySelector('p');
    const timerBox  = document.getElementById('timer-container');

    const cs = getComputedStyle(container);
    const innerW = container.clientWidth
                 - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);

    const maxWidth = Math.min(innerW, window.innerWidth * 0.94);

    const wordsH = wordsBox ? wordsBox.offsetHeight : 0;
    const headerH = (titleEl?.offsetHeight || 0) + (subEl?.offsetHeight || 0) + (timerBox?.offsetHeight || 0);
    const containerVPadding = parseFloat(cs.paddingTop) + parseFloat(cs.paddingBottom);
    const verticalMargins = 40;
    const availableH = window.innerHeight - headerH - wordsH - containerVPadding - verticalMargins;

    const cellByWidth  = (maxWidth  - (cols - 1) * gap - 2 * gap) / cols;
    const cellByHeight = (availableH - (rows - 1) * gap - 2 * gap) / rows;

    const cell = Math.floor(Math.min(cellByWidth, cellByHeight));
    const finalSize = Math.max(22, Math.min(cell, 60));

    root.style.setProperty('--cell-size', finalSize + 'px');
    root.style.setProperty('--cols', cols);
    root.style.setProperty('--rows', rows);
    root.style.setProperty('--gap', gap + 'px');
  }

  window.addEventListener('resize', adjustGrid);
  adjustGrid();
})();

/* ===== Inicio ===== */
(function init() {
  createFixedBoard();
  fillRandom();
  render();
  updateStatus();
  startTimer();
})();
