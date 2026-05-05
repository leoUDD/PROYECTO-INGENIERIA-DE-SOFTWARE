const skills = [
  {
    e: '🤝',
    name: 'TRABAJO EN EQUIPO',
    sub: 'COLABORACIÓN',
    c: '#ff6600',
    desc: 'Escucha, comparte y avancen como uno solo. Un equipo sincronizado es el arma más poderosa de la misión.',
    pills: ['Escucha activa', 'Meta común', 'Apoyo mutuo']
  },
  {
    e: '💙',
    name: 'EMPATÍA',
    sub: 'COMPRENSIÓN',
    c: '#00c8ff',
    desc: 'Antes de actuar, entiende. Qué siente, qué necesita, qué teme la persona que buscas ayudar.',
    pills: ['¿Qué siente?', '¿Qué necesita?', '¿Qué espera?']
  },
  {
    e: '💡',
    name: 'CREATIVIDAD',
    sub: 'INNOVACIÓN',
    c: '#ffd700',
    desc: 'Las soluciones obvias no bastan. Piensa diferente, combina lo inesperado, sorprende al mundo.',
    pills: ['Ideas atrevidas', 'Combinar todo', 'Iterar rápido']
  },
  {
    e: '📢',
    name: 'COMUNICACIÓN',
    sub: 'EXPRESIÓN',
    c: '#ff4455',
    desc: 'Una idea brillante que nadie entiende no existe. Sé claro, directo y convincente en cada mensaje.',
    pills: ['Claridad', 'Impacto visual', 'Convicción']
  },
  {
    e: '🛡️',
    name: 'APOYO',
    sub: 'MEJORA CONTINUA',
    c: '#44dd88',
    desc: 'Evalúa, ajusta y crece. El feedback honesto es el entrenamiento más duro y más valioso.',
    pills: ['Evaluación', 'Feedback honesto', 'Adaptación']
  },
];

const ROUTE = [
  { fx: .15, fy: .22 },
  { fx: .80, fy: .20 },
  { fx: .46, fy: .54 },
  { fx: .13, fy: .78 },
  { fx: .82, fy: .76 },
];

const SPEEDS = ['3.2s', '2.9s', '3.7s', '3.0s', '2.7s'];
const DELAYS = ['0s', '.6s', '1.1s', '.3s', '.9s'];

let done = new Set();
let activeIdx = null;

function rpx(f, t) { return Math.round(f * t); }

// ── SONIDO HOVER ────────────────────────────────────────────────
function playHoverSound() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const now = ctx.currentTime;
    const osc = ctx.createOscillator(), gain = ctx.createGain();
    osc.connect(gain); gain.connect(ctx.destination);
    osc.type = 'sine';
    osc.frequency.setValueAtTime(280, now);
    osc.frequency.linearRampToValueAtTime(520, now + 0.12);
    gain.gain.setValueAtTime(0.07, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.14);
    osc.start(now); osc.stop(now + 0.15);
    const osc2 = ctx.createOscillator(), gain2 = ctx.createGain();
    osc2.connect(gain2); gain2.connect(ctx.destination);
    osc2.type = 'triangle';
    osc2.frequency.setValueAtTime(560, now + 0.06);
    osc2.frequency.linearRampToValueAtTime(800, now + 0.14);
    gain2.gain.setValueAtTime(0.03, now + 0.06);
    gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.16);
    osc2.start(now + 0.06); osc2.stop(now + 0.17);
  } catch(e) {}
}

// ── SONIDO CLICK ────────────────────────────────────────────────
function playClickSound() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const now = ctx.currentTime;
    const bufLen = Math.floor(ctx.sampleRate * 0.03);
    const buf    = ctx.createBuffer(1, bufLen, ctx.sampleRate);
    const data   = buf.getChannelData(0);
    for (let i = 0; i < bufLen; i++)
      data[i] = (Math.random() * 2 - 1) * Math.exp(-i / 50);
    const noise = ctx.createBufferSource(), noiseGain = ctx.createGain();
    noise.buffer = buf; noise.connect(noiseGain); noiseGain.connect(ctx.destination);
    noiseGain.gain.value = 0.25; noise.start(now);
    const osc = ctx.createOscillator(), gain = ctx.createGain();
    osc.connect(gain); gain.connect(ctx.destination);
    osc.type = 'sine';
    osc.frequency.setValueAtTime(180, now + 0.02);
    osc.frequency.exponentialRampToValueAtTime(90, now + 0.18);
    gain.gain.setValueAtTime(0.18, now + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.20);
    osc.start(now + 0.02); osc.stop(now + 0.22);
    [{ t: 0.22, f: 440 }, { t: 0.32, f: 660 }].forEach(({ t, f }) => {
      const o = ctx.createOscillator(), g = ctx.createGain();
      o.connect(g); g.connect(ctx.destination);
      o.type = 'sine'; o.frequency.value = f;
      g.gain.setValueAtTime(0.10, now + t);
      g.gain.exponentialRampToValueAtTime(0.001, now + t + 0.08);
      o.start(now + t); o.stop(now + t + 0.09);
    });
  } catch(e) {}
}

// ── MAPA ────────────────────────────────────────────────────────
function build() {
  const wrap = document.getElementById('map-wrap');
  const W = wrap.offsetWidth, H = wrap.offsetHeight;
  if (!W || !H) { setTimeout(build, 100); return; }

  const svg = document.getElementById('msvg');
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);

  const pts = ROUTE.map(r => ({ x: rpx(r.fx, W), y: rpx(r.fy, H) }));

  let grid = '';
  for (let x = 0; x < W; x += 80)
    grid += `<line x1="${x}" y1="0" x2="${x}" y2="${H}" stroke="rgba(140,200,255,.35)" stroke-width="1"/>`;
  for (let y = 0; y < H; y += 80)
    grid += `<line x1="0" y1="${y}" x2="${W}" y2="${y}" stroke="rgba(140,200,255,.35)" stroke-width="1"/>`;

  let rings = '';
  [[0,0],[1,0],[0,1],[1,1]].forEach(([fx, fy]) => {
    const cx = fx === 0 ? 32 : W - 32;
    const cy = fy === 0 ? 32 : H - 32;
    [20, 36, 52].forEach(r => {
      rings += `<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="rgba(40,100,255,.1)" stroke-width="1"/>`;
    });
    rings += `<line x1="${cx-16}" y1="${cy}" x2="${cx+16}" y2="${cy}" stroke="rgba(40,100,255,.12)" stroke-width="1"/>`;
    rings += `<line x1="${cx}" y1="${cy-16}" x2="${cx}" y2="${cy+16}" stroke="rgba(40,100,255,.12)" stroke-width="1"/>`;
  });

  let pathD = `M${pts[0].x},${pts[0].y}`;
  for (let i = 1; i < pts.length; i++) {
    const a = pts[i-1], b = pts[i];
    const cx = (a.x + b.x) / 2;
    const cy = (a.y + b.y) / 2 - Math.abs(b.x - a.x) * .18;
    pathD += ` Q${cx},${cy} ${b.x},${b.y}`;
  }

  svg.innerHTML = grid + rings +
    `<path d="${pathD}" fill="none" stroke="rgba(64,128,255,.2)" stroke-width="3" stroke-dasharray="10 7"/>` +
    `<path d="${pathD}" fill="none" stroke="rgba(64,128,255,.07)" stroke-width="18"/>`;

  document.querySelectorAll('.nd').forEach(n => n.remove());

  pts.forEach((p, i) => {
    const s = skills[i];
    const isDone   = done.has(i);
    const isLocked = i > 0 && !done.has(i - 1) && !isDone;

    const nd = document.createElement('div');
    nd.className = 'nd' + (isDone ? ' done' : '') + (isLocked ? ' locked' : '');
    nd.id = 'nd' + i;
    nd.style.cssText = `left:${p.x}px;top:${p.y}px;--c:${s.c};--spd:${SPEEDS[i]};--dly:${DELAYS[i]};`;
    nd.innerHTML = `
      <div class="nd-outer">
        <div class="nd-pulse"></div>
        <div class="nd-icon">${s.e}</div>
        <div class="nd-check">✓</div>
        <div class="nd-lock">🔒</div>
      </div>
      <div class="nd-lbl">${s.name}</div>
    `;

    // Sonido hover (solo si no está bloqueado)
    nd.addEventListener('mouseenter', () => {
      if (!nd.classList.contains('locked')) playHoverSound();
    });

    // Sonido + acción al click
    nd.onclick = () => {
      if (!nd.classList.contains('locked')) playClickSound();
      openSkill(i);
    };

    document.getElementById('map-wrap').appendChild(nd);
  });

  moveDot(activeIdx !== null ? activeIdx : (done.size ? Math.max(...done) : 0), false);
  buildPips();
}

function buildPips() {
  const c = document.getElementById('pips');
  c.innerHTML = '';
  skills.forEach((_, i) => {
    const d = document.createElement('div');
    d.className = 'pip' + (done.has(i) ? ' done' : '');
    c.appendChild(d);
  });
}

// Almacena el índice actual del dot para animar desde ahí
let dotCurrentIdx = 0;

function moveDot(idx, animate) {
  const wrap = document.getElementById('map-wrap');
  const W = wrap.offsetWidth, H = wrap.offsetHeight;
  const dot = document.getElementById('pdot');

  if (!animate) {
    const r = ROUTE[idx];
    dot.style.transition = 'none';
    dot.style.left = rpx(r.fx, W) + 'px';
    dot.style.top  = rpx(r.fy, H) + 'px';
    dotCurrentIdx = idx;
    return;
  }

  // Construir el path SVG en memoria para medir distancias
  const pts = ROUTE.map(r => ({ x: rpx(r.fx, W), y: rpx(r.fy, H) }));
  const ns = 'http://www.w3.org/2000/svg';
  const tmpSvg = document.createElementNS(ns, 'svg');
  const tmpPath = document.createElementNS(ns, 'path');

  let d = `M${pts[0].x},${pts[0].y}`;
  for (let i = 1; i < pts.length; i++) {
    const a = pts[i-1], b = pts[i];
    const cx = (a.x + b.x) / 2;
    const cy = (a.y + b.y) / 2 - Math.abs(b.x - a.x) * .18;
    d += ` Q${cx},${cy} ${b.x},${b.y}`;
  }
  tmpPath.setAttribute('d', d);
  tmpSvg.style.cssText = 'position:absolute;visibility:hidden;pointer-events:none;top:0;left:0;width:0;height:0;overflow:hidden;';
  tmpSvg.appendChild(tmpPath);
  document.body.appendChild(tmpSvg);

  const totalLength = tmpPath.getTotalLength();

  // Calcular longitud acumulada hasta cada nodo
  function lengthAtNode(i) {
    const tempD_ns = 'http://www.w3.org/2000/svg';
    const s = document.createElementNS(tempD_ns, 'svg');
    const p = document.createElementNS(tempD_ns, 'path');
    let pd = `M${pts[0].x},${pts[0].y}`;
    for (let j = 1; j <= i; j++) {
      const a = pts[j-1], b = pts[j];
      const cx = (a.x + b.x) / 2;
      const cy = (a.y + b.y) / 2 - Math.abs(b.x - a.x) * .18;
      pd += ` Q${cx},${cy} ${b.x},${b.y}`;
    }
    p.setAttribute('d', pd);
    s.style.cssText = 'position:absolute;visibility:hidden;pointer-events:none;top:0;left:0;width:0;height:0;overflow:hidden;';
    s.appendChild(p);
    document.body.appendChild(s);
    const len = p.getTotalLength();
    document.body.removeChild(s);
    return len;
  }

  const fromLen = dotCurrentIdx === idx ? 0 : lengthAtNode(Math.min(dotCurrentIdx, idx));
  const toLen   = lengthAtNode(idx);
  document.body.removeChild(tmpSvg);

  // Animar el punto a lo largo del path
  const duration = 1200;
  const start = performance.now();

  // Reconstruir path para animar
  const animPts = ROUTE.map(r => ({ x: rpx(r.fx, W), y: rpx(r.fy, H) }));
  const animNs = 'http://www.w3.org/2000/svg';
  const animSvg = document.createElementNS(animNs, 'svg');
  const animPath = document.createElementNS(animNs, 'path');
  let animD = `M${animPts[0].x},${animPts[0].y}`;
  for (let i = 1; i < animPts.length; i++) {
    const a = animPts[i-1], b = animPts[i];
    const cx = (a.x + b.x) / 2;
    const cy = (a.y + b.y) / 2 - Math.abs(b.x - a.x) * .18;
    animD += ` Q${cx},${cy} ${b.x},${b.y}`;
  }
  animPath.setAttribute('d', animD);
  animSvg.style.cssText = 'position:absolute;visibility:hidden;pointer-events:none;top:0;left:0;width:0;height:0;overflow:hidden;';
  animSvg.appendChild(animPath);
  document.body.appendChild(animSvg);

  dot.style.transition = 'none';

  function easeInOut(t) {
    return t < 0.5 ? 2*t*t : -1+(4-2*t)*t;
  }

  function step(now) {
    const elapsed = now - start;
    const t = Math.min(elapsed / duration, 1);
    const eased = easeInOut(t);
    const currentLen = fromLen + (toLen - fromLen) * eased;
    const pt = animPath.getPointAtLength(currentLen);
    dot.style.left = pt.x + 'px';
    dot.style.top  = pt.y + 'px';
    if (t < 1) {
      requestAnimationFrame(step);
    } else {
      document.body.removeChild(animSvg);
      dotCurrentIdx = idx;
    }
  }

  requestAnimationFrame(step);
}

function openSkill(idx) {
  if (idx > 0 && !done.has(idx - 1) && !done.has(idx)) return;
  activeIdx = idx;
  moveDot(idx, true);

  const s = skills[idx];
  document.getElementById('pempty').style.display = 'none';

  const card = document.getElementById('pcard');
  card.classList.remove('show');
  card.style.display = 'none';
  void card.offsetWidth;

  document.getElementById('pc-em').textContent   = s.e;
  document.getElementById('pc-name').textContent = s.name;
  document.getElementById('pc-desc').textContent = s.desc;

  const sub = document.getElementById('pc-sub');
  sub.textContent = s.sub;
  sub.style.color = s.c;

  document.getElementById('pc-pills').innerHTML =
    s.pills.map(p => `<div class="pll">${p}</div>`).join('');

  const btn = document.getElementById('pc-btn');
  if (done.has(idx)) {
    btn.textContent = '[ HABILIDAD CONFIRMADA ✓ ]';
    btn.classList.add('confirmed');
  } else {
    btn.textContent = '[ ENTENDIDO ]';
    btn.classList.remove('confirmed');
  }

  card.style.display = 'flex';
  requestAnimationFrame(() => card.classList.add('show'));
}

function markDone() {
  if (activeIdx === null) return;
  playClickSound();
  done.add(activeIdx);

  document.getElementById('pc-btn').textContent = '[ HABILIDAD CONFIRMADA ✓ ]';
  document.getElementById('pc-btn').classList.add('confirmed');

  const nd = document.getElementById('nd' + activeIdx);
  if (nd) { nd.classList.add('done'); nd.classList.remove('locked'); }

  const next = activeIdx + 1;
  if (next < skills.length) {
    const nnd = document.getElementById('nd' + next);
    if (nnd) { nnd.classList.remove('locked'); nnd.style.pointerEvents = 'all'; }
  }

  buildPips();

  if (done.size === skills.length) {
    const btn = document.getElementById('bt-btn');
    btn.classList.add('ready');
    document.getElementById('bt-hint').textContent = '// TODAS LAS HABILIDADES CONFIRMADAS — AGENTE LISTO';
  }

  if (next < skills.length) setTimeout(() => openSkill(next), 500);
}

// ── MÚSICA DE FONDO ─────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const music = document.getElementById('bg-music');
  if (!music) return;
  music.volume = 0.4;

  function startMusic() {
    music.play().catch(() => {});
    document.removeEventListener('click', startMusic);
    document.removeEventListener('keydown', startMusic);
  }

  music.play().catch(() => {
    document.addEventListener('click', startMusic);
    document.addEventListener('keydown', startMusic);
  });

  // Sonido en botón ENTENDIDO
  const pcBtn = document.getElementById('pc-btn');
  if (pcBtn) pcBtn.addEventListener('mouseenter', playHoverSound);

  // Sonido en botón INICIAR MISIÓN
  const btBtn = document.getElementById('bt-btn');
  if (btBtn) {
    btBtn.addEventListener('mouseenter', playHoverSound);
    btBtn.addEventListener('click', playClickSound);
  }
});

window.addEventListener('resize', build);
setTimeout(build, 80);