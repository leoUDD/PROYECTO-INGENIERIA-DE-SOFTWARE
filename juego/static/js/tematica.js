document.addEventListener("DOMContentLoaded", () => {
  const track = document.getElementById("themesTrack");
  const prev = document.querySelector(".carousel-btn.prev");
  const next = document.querySelector(".carousel-btn.next");

  function moverCarrusel(direccion) {
    if (!track) return;
    const primera = track.querySelector(".theme-card");
    if (!primera) return;

    const ancho = primera.offsetWidth + 24;
    track.scrollLeft += direccion * ancho;
  }

  prev?.addEventListener("click", (e) => {
    e.preventDefault();
    moverCarrusel(-1);
  });

  next?.addEventListener("click", (e) => {
    e.preventDefault();
    moverCarrusel(1);
  });
});