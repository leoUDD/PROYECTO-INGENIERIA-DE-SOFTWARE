document.addEventListener("DOMContentLoaded", () => {
  iniciarMusicaFondo();
  iniciarSonidoHoverTarjetas();
});

function iniciarMusicaFondo() {
  const musicaFondo = document.getElementById("musica-fondo");

  if (!musicaFondo) return;

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

let audioCtx = null;

function getAudioCtx() {
  if (!audioCtx || audioCtx.state === "closed") {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  }

  return audioCtx;
}

function playHoverSound() {
  try {
    const ctx = getAudioCtx();
    const now = ctx.currentTime;

    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.type = "sine";
    osc.frequency.setValueAtTime(320, now);
    osc.frequency.linearRampToValueAtTime(520, now + 0.1);

    gain.gain.setValueAtTime(0.08, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.18);

    osc.start(now);
    osc.stop(now + 0.2);
  } catch (e) {}
}

function iniciarSonidoHoverTarjetas() {
  document.querySelectorAll(".mode-card").forEach((card) => {
    card.addEventListener("mouseenter", playHoverSound);
  });
}