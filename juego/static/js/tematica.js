document.addEventListener("DOMContentLoaded", () => {
  const cards = Array.from(document.querySelectorAll(".theme-card"));
  const cta = document.getElementById("btnContinuar");
  const track = document.getElementById("themesTrack");
  const prev = document.querySelector(".carousel-btn.prev");
  const next = document.querySelector(".carousel-btn.next");

  function norm(valor) {
    return (valor || "").toString().trim().toLowerCase();
  }

  function actualizarBotones(cardSeleccionada) {
    const botones = document.querySelectorAll(".theme-card .btn.select");

    botones.forEach(btn => {
      btn.textContent = "Elegir";
      btn.disabled = false;
    });

    if (cardSeleccionada) {
      const btn = cardSeleccionada.querySelector(".btn.select");
      if (btn) {
        btn.textContent = "Seleccionado ✅";
        btn.disabled = true;
      }
    }
  }

  function seleccionarTema(slugRaw) {
    const slug = norm(slugRaw);
    const card = cards.find(c => norm(c.dataset.slug) === slug);
    if (!card) return;

    cards.forEach(c => c.classList.remove("selected"));
    card.classList.add("selected");

    localStorage.setItem("temaSeleccionado", slug);

    if (cta) cta.disabled = false;
    actualizarBotones(card);
  }

  window.guardarTema = function (slugRaw) {
    seleccionarTema(slugRaw);
  };

  const temaGuardado = localStorage.getItem("temaSeleccionado");
  if (temaGuardado) {
    seleccionarTema(temaGuardado);
  } else if (cta) {
    cta.disabled = true;
  }

  function moverCarrusel(direccion) {
    if (!track) return;
    const primera = track.querySelector(".theme-card");
    if (!primera) return;

    const ancho = primera.offsetWidth + 24;
    track.scrollLeft += direccion * ancho;
  }

  if (prev) {
    prev.addEventListener("click", (e) => {
      e.preventDefault();
      moverCarrusel(-1);
    });
  }

  if (next) {
    next.addEventListener("click", (e) => {
      e.preventDefault();
      moverCarrusel(1);
    });
  }
});