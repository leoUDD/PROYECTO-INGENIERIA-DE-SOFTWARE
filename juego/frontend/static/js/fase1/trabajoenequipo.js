document.addEventListener("DOMContentLoaded", () => {
  iniciarMusicaFondo();
  iniciarTrabajoEquipo();
});

function tJuego(clave, fallback = "") {
  const idioma = window.i18nJuego?.obtenerIdioma?.() || "es";
  return window.i18nJuego?.traducciones?.[idioma]?.[clave] || fallback;
}

function iniciarMusicaFondo() {
  const musicaFondo = document.getElementById("musica-fondo");

  if (!musicaFondo) return;

  musicaFondo.volume = 0.35;

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

function iniciarTrabajoEquipo() {
  const routesEl = document.getElementById("routes");
  const boton = document.getElementById("btn-listo-f1");
  const estado = document.getElementById("estado-listo-f1");

  const sesionId = routesEl?.dataset?.sesionId;
  const grupoId = routesEl?.dataset?.grupoId;
  const csrfToken = routesEl?.dataset?.csrfToken;

  let yaListo = false;
  let redirigiendo = false;

  if (!routesEl || !boton || !estado || !sesionId || !grupoId || !csrfToken) return;

  function textoGruposListos(listos, total) {
    return `${listos}/${total} ${tJuego("trabajo_equipo_grupos_listos", "grupos listos")}`;
  }

  function textoEsperando() {
    return tJuego("trabajo_equipo_boton_esperando", "Esperando...");
  }

  function textoListo() {
    return tJuego("trabajo_equipo_boton", "⚡ Listo para continuar");
  }

  function actualizarEstadoListos(data) {
    const listos =
      data.gruposListosF1 ??
      data.gruposListos ??
      data.listos ??
      0;

    const total =
      data.totalGrupos ??
      data.total ??
      0;

    estado.textContent = textoGruposListos(listos, total);
  }

  function marcarBotonComoListo() {
    yaListo = true;
    boton.disabled = true;
    boton.textContent = textoEsperando();
  }

  function sincronizarMiGrupo(data) {
    const miGrupo = (data.grupos || []).find((g) => Number(g.id) === Number(grupoId));

    if (!miGrupo) return;

    if (
      miGrupo.listoF1 ||
      miGrupo.listo_f1 ||
      miGrupo.listo
    ) {
      marcarBotonComoListo();
    }
  }

  function revisarRedireccion(data) {
    if (!data.faseActual) return;

    if (data.faseActual !== "f1_pre_sopa") {
      if (data.rutaAlumno && window.location.pathname !== data.rutaAlumno) {
        redirigiendo = true;
        window.location.href = data.rutaAlumno;
      }
    }
  }

  async function consultarEstadoSesion() {
    if (redirigiendo) return;

    try {
      const res = await fetch(`/sesion/${sesionId}/estado/`, {
        cache: "no-store",
        credentials: "same-origin",
      });

      if (!res.ok) return;

      const data = await res.json();

      actualizarEstadoListos(data);
      sincronizarMiGrupo(data);
      revisarRedireccion(data);
    } catch (error) {
      console.error("Error consultando estado de trabajo en equipo:", error);
    }
  }

  boton.addEventListener("click", async () => {
    if (yaListo || redirigiendo) return;

    marcarBotonComoListo();

    try {
      const res = await fetch(`/grupo/${grupoId}/listo/`, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({ fase: "f1" }),
      });

      const data = await res.json();

      if (!res.ok || data.ok === false) {
        throw new Error(data.error || "No se pudo marcar listo.");
      }

      actualizarEstadoListos(data);
      revisarRedireccion(data);

      if (data.todos_listos || data.todosListosF1) {
        await consultarEstadoSesion();
      }
    } catch (error) {
      console.error("Error marcando listo en trabajo en equipo:", error);

      yaListo = false;
      boton.disabled = false;
      boton.textContent = textoListo();
    }
  });

  window.addEventListener("idiomaJuegoCambiado", () => {
    boton.textContent = boton.disabled ? textoEsperando() : textoListo();

    const match = estado.textContent.match(/(\d+)\/(\d+)/);

    if (match) {
      estado.textContent = textoGruposListos(match[1], match[2]);
    }
  });

  consultarEstadoSesion();
  setInterval(consultarEstadoSesion, 1500);
}