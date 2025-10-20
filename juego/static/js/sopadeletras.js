// === CONFIGURACIÓN (fija) ===
const gridSize = 12;
const words = ["IDEA", "EQUIPO", "NEGOCIO", "CREATIVIDAD", "LIDERAZGO"];
const gridEl = document.getElementById("grid");
const statusEl = document.getElementById("status");

// sincroniza columnas con el CSS (usa :root { --cols: 12; } en tu CSS)
document.documentElement.style.setProperty('--cols', gridSize);

// 8 direcciones: horizontales, verticales y diagonales
const DIRS = [
  [1, 0],  [-1, 0],  [0, 1],  [0, -1],
  [1, 1],  [-1, -1], [1, -1], [-1, 1]
];

let board = [];
let mouseDown = false;
let selection = [];

// === Tablero fijo: 12x12. Las 'X' se rellenan con letras al azar ===
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

// Rellena las X con letras aleatorias
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

// Dibuja la grilla y conecta eventos
function render() {
  gridEl.innerHTML = "";
  for (let r = 0; r < gridSize; r++) {
    for (let c = 0; c < gridSize; c++) {
      const cell = document.createElement("div");
      cell.className = "cell";
      cell.textContent = board[r][c];
      cell.dataset.r = r;
      cell.dataset.c = c;

      cell.addEventListener("mousedown", handleDown);
      cell.addEventListener("mouseover", handleOver);
      cell.addEventListener("mouseup", handleUp);

      gridEl.appendChild(cell);
    }
  }
  document.addEventListener("mouseup", cancelDragOutside);
}

// ===== Manejo de selección (click + arrastre en línea recta) =====
function handleDown(e) {
  if (e.button !== 0) return; // solo click izquierdo
  mouseDown = true;
  clearTempSelection();
  addToSelection(e.currentTarget);
}

function handleOver(e) {
  if (!mouseDown) return;
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
  const r = parseInt(el.dataset.r, 10);
  const c = parseInt(el.dataset.c, 10);

  // evitar duplicar celdas
  if (selection.some(s => s.r === r && s.c === c)) return;

  // Mantener línea recta (8 direcciones)
  if (validateLine && selection.length >= 1) {
    const r0 = selection[0].r, c0 = selection[0].c;
    const dr = r - r0, dc = c - c0;
    const gcd = (a, b) => b ? gcd(b, a % b) : Math.abs(a);
    const g = gcd(Math.abs(dr), Math.abs(dc)) || 1;
    const udr = dr / g, udc = dc / g;
    const isValidDir = DIRS.some(([dx, dy]) => dx === udc && dy === udr);
    if (!isValidDir) return; // no permitir quiebres
  }

  el.classList.add("selected");
  selection.push({ r, c, el });
}

function clearTempSelection() {
  selection.forEach(s => s.el.classList.remove("selected"));
  selection = [];
}

// Convierte la selección en texto (ordenada a lo largo de la línea)
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

// Verifica si la selección coincide con una palabra (normal o al revés)
function checkSelection() {
  if (selection.length === 0) return;

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
      setTimeout(showWinModal, 200);
    }
  } else {
    clearTempSelection();
  }
}

// ===== Utilidades para la lista (robustas con o sin data-word) =====
function getWordListItem(word) {
  // 1) Intentar por data-word exacto
  let li = document.querySelector(`#word-list li[data-word="${word}"]`);
  if (li) return li;

  // 2) Fallback: buscar por texto del li en mayúsculas
  const items = document.querySelectorAll('#word-list li');
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
  if (!statusEl) return; // por si no existe el contador en el HTML
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
function showWinModal(){
  const modal = document.getElementById('winModal');
  const btn = document.getElementById('btnNext');
  if (!modal || !btn) return;

  modal.style.display = 'flex';
  modal.setAttribute('aria-hidden', 'false');

  launchConfetti(7000, 700); // Celebración
  setTimeout(() => {launchConfetti(6000, 500);}, 1200);
  setTimeout(() => {launchConfetti(5000, 400);}, 2500);

  // Enfocar el botón para accesibilidad
  setTimeout(() => btn.focus(), 50);

  // Cerrar con ESC si quisieras (opcional)
  document.addEventListener('keydown', onEscClose);

  // Acción del botón: redirigir a la siguiente etapa
  btn.addEventListener('click', goNext, { once: true });

  function onEscClose(e){
    if (e.key === 'Escape'){
      modal.style.display = 'none';
      modal.setAttribute('aria-hidden', 'true');
      document.removeEventListener('keydown', onEscClose);
    }
  }
}
// Confeti vanilla: canvas temporal + partículas animadas
function launchConfetti(durationMs = 1000, particleCount = 160) {
  // Crear canvas overlay
  const canvas = document.createElement('canvas');
  canvas.id = 'confetti-canvas';
  document.body.appendChild(canvas);

  const ctx = canvas.getContext('2d');
  let W = canvas.width = window.innerWidth;
  let H = canvas.height = window.innerHeight;

  const onResize = () => {
    W = canvas.width = window.innerWidth;
    H = canvas.height = window.innerHeight;
  };
  window.addEventListener('resize', onResize);

  // Paleta y partículas
  const colors = ['#FFC700','#FF2D55','#00D4FF','#4B74AA','#16A34A'];
  const GRAV = 0.18;       // gravedad
  const DRAG = 0.995;      // rozamiento
  const FADE = 0.012;      // velocidad de desvanecimiento

  const particles = [];
  // Emitir desde múltiples posiciones (centro y bordes)
const emitters = [
  { x: W / 2, y: H * 0.2 },   // centro arriba
  { x: W * 0.1, y: H * 0.3 }, // izquierda
  { x: W * 0.9, y: H * 0.3 }, // derecha
  { x: W / 2, y: H * 0.8 }    // parte baja
];

// combinar todas las partículas de los emisores
for (const em of emitters) {
  for (let i = 0; i < particleCount / emitters.length; i++) {
    const angle = (Math.random() * Math.PI * 2); // 360°
    const speed = 4 + Math.random() * 6;
    particles.push({
      x: em.x + (Math.random() * 30 - 15),
      y: em.y + (Math.random() * 30 - 15),
      vx: Math.cos(angle) * speed,
      vy: Math.sin(angle) * speed - 1,
      size: 6 + Math.random() * 4,
      rot: Math.random() * Math.PI,
      vr: (Math.random() - 0.5) * 0.3,
      color: colors[(Math.random() * colors.length) | 0],
      alpha: 1
    });
  }
}


  let start = null;
  function frame(ts){
    if (!start) start = ts;
    const elapsed = ts - start;

    ctx.clearRect(0, 0, W, H);

    for (const p of particles) {
      // física
      p.vx *= DRAG;
      p.vy = p.vy * DRAG + GRAV;
      p.x += p.vx;
      p.y += p.vy;
      p.rot += p.vr;
      p.alpha -= FADE;

      // dibujo
      if (p.alpha > 0 && p.y < H + 40) {
        ctx.globalAlpha = Math.max(0, p.alpha);
        ctx.fillStyle = p.color;
        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate(p.rot);
        // rectángulos “papel picado”
        ctx.fillRect(-p.size/2, -p.size/2, p.size, p.size * 0.6);
        ctx.restore();
      } else {
        p.alpha = 0;
      }
    }

    // continuar mientras dure la animación y haya algo visible
    if (elapsed < durationMs && particles.some(p => p.alpha > 0)) {
      requestAnimationFrame(frame);
    } else {
      cleanup();
    }
  }

  function cleanup(){
    window.removeEventListener('resize', onResize);
    canvas.remove();
  }

  requestAnimationFrame(frame);
}

function goNext(){
    window.location.href = "{% url '#' %}";
}
// ===== TEMPORIZADOR (2 minutos = 120s) =====
let timeLeft = 120;
let timerInterval;

function startTimer() {
  const timerEl = document.getElementById('timer');
  if (!timerEl) return;

  function updateTimer() {
    const min = Math.floor(timeLeft / 60);
    const sec = timeLeft % 60;
    timerEl.textContent = `${min.toString().padStart(2,'0')}:${sec.toString().padStart(2,'0')}`;

    // efecto visual al quedar menos de 10s
    if (timeLeft <= 10) {
      timerEl.classList.add('low-time');
    }

    if (timeLeft <= 0) {
      clearInterval(timerInterval);
      showTimeUpModal();
      reproducirAlarma();
    } else {
      timeLeft--;
    }
  }

  updateTimer(); // primera actualización inmediata
  timerInterval = setInterval(updateTimer, 1000);
}

// Mostrar modal de tiempo terminado
function showTimeUpModal() {
  const modal = document.getElementById('timeModal');
  const btn = document.getElementById('btnRetry');
  if (!modal || !btn) return;

  modal.style.display = 'flex';
  modal.setAttribute('aria-hidden', 'false');
  

  btn.addEventListener('click', () => {
    window.location.href = "{% url '#' %}";
  }, { once: true });
}
function reproducirAlarma() {
        const alarmAudio = document.getElementById('alarm-audio');
        alarmAudio.currentTime = 0;
        alarmAudio.play();

        const body = document.body;
        body.classList.add('flash');
        setTimeout(() => {body.classList.remove('flash');}, 800);
      }
// ===== Inicio =====
(function init() {
  startTimer();
  createFixedBoard();
  fillRandom();   // reemplaza las 'X'
  render();       // dibuja tablero
  updateStatus(); // 0/n al inicio
})();
