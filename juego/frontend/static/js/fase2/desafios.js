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

document.addEventListener("DOMContentLoaded", () => {
  function tJuego(clave, fallback = "") {
    const idioma = window.i18nJuego?.obtenerIdioma?.() || "es";
    return window.i18nJuego?.traducciones?.[idioma]?.[clave] || fallback;
  }

  function textoElegir() {
    return tJuego("desafios_elegir", "Elegir");
  }

  function textoConfirmado() {
    return tJuego("desafios_confirmado", "Confirmado");
  }

  function textoGruposListos(listos, total) {
    return `${listos}/${total} ${tJuego("desafios_grupos_listos", "grupos listos")}`;
  }

  function textoConfirmarDesafio(nombre) {
    const idioma = window.i18nJuego?.obtenerIdioma?.() || "es";

    if (idioma === "en") {
      return `Confirm the challenge "${nombre}" for your team?`;
    }

    return `¿Confirmar el desafío "${nombre}" para tu equipo?`;
  }

  const botones = document.querySelectorAll("[data-desafio-id]");
  const cards = document.querySelectorAll(".challenge-card");

  const estadoSeleccion = document.getElementById("estadoSeleccion");
  const nombreDesafio = document.getElementById("nombreDesafioSeleccionado");
  const descripcionDesafio = document.getElementById("descripcionDesafioSeleccionado");
  const desafioData = document.getElementById("desafio-data");
  const estadoError = document.getElementById("estadoError");
  const contador = document.getElementById("contadorGruposListos");
  const timerTematica = document.getElementById("timerTematica");

  const sesionId = document.body.dataset.sesionId;
  const grupoId = document.body.dataset.grupoId;

  const guardarDesafioUrl = desafioData?.dataset?.guardarDesafioUrl;

  const desafioConfirmado = desafioData?.dataset?.desafioConfirmado === "true";
  const desafioIdActual = desafioData?.dataset?.desafioIdActual || "";
  const desafioNombreActual = desafioData?.dataset?.desafioNombreActual || "";
  const desafioDescripcionActual = desafioData?.dataset?.desafioDescripcionActual || "";

  let enviando = false;
  let bloqueado = desafioConfirmado;
  let redirigiendo = false;
  let ultimoListos = 0;
  let ultimoTotal = 0;
  let desafioBloqueadoActual = desafioIdActual;

  function formatearTiempo(segundos) {
    segundos = Math.max(Number(segundos || 0), 0);

    const min = Math.floor(segundos / 60);
    const seg = segundos % 60;

    return `${min}:${String(seg).padStart(2, "0")}`;
  }

  function mostrarError(texto) {
    if (!estadoError) return;

    if (!texto) {
      estadoError.classList.remove("visible");
      estadoError.textContent = "";
      return;
    }

    estadoError.textContent = texto;
    estadoError.classList.add("visible");
  }

  function actualizarContador(data) {
    const listos = Number(data?.gruposListosF2 || 0);
    const total = Number(data?.totalGrupos || 0);

    ultimoListos = listos;
    ultimoTotal = total;

    if (contador) {
      contador.textContent = textoGruposListos(listos, total);
    }
  }

  function marcarSeleccion(cardId) {
    cards.forEach((card) => {
      card.classList.remove("seleccionado");
    });

    const card = document.getElementById(cardId);

    if (card) {
      card.classList.add("seleccionado");
    }
  }

  function aplicarTextoBotones() {
    botones.forEach((boton) => {
      const esElegido = boton.dataset.desafioId === String(desafioBloqueadoActual);

      if (bloqueado) {
        boton.textContent = esElegido ? textoConfirmado() : textoElegir();
      } else {
        boton.textContent = textoElegir();
      }
    });
  }

  function aplicarModoBloqueado(desafioId, nombre, descripcion) {
    bloqueado = true;
    desafioBloqueadoActual = String(desafioId || "");

    mostrarError("");

    botones.forEach((boton) => {
      const esElegido = boton.dataset.desafioId === String(desafioId);

      boton.disabled = true;
      boton.textContent = esElegido ? textoConfirmado() : textoElegir();
    });

    cards.forEach((card) => {
      if (String(card.dataset.id) === String(desafioId)) {
        card.classList.add("seleccionado", "bloqueada");
      } else {
        card.classList.remove("seleccionado");
        card.classList.add("bloqueada");
      }
    });

    if (nombreDesafio) {
      nombreDesafio.textContent = nombre || "-";
    }

    if (descripcionDesafio) {
      descripcionDesafio.textContent = descripcion || "";
    }

    if (estadoSeleccion) {
      estadoSeleccion.classList.add("visible");
    }

    marcarSeleccion(`card-${desafioId}`);
  }

  function aplicarModoEditable() {
    bloqueado = false;
    desafioBloqueadoActual = "";

    mostrarError("");

    botones.forEach((boton) => {
      boton.disabled = false;
      boton.textContent = textoElegir();
    });

    cards.forEach((card) => {
      card.classList.remove("bloqueada", "seleccionado");
    });

    if (estadoSeleccion) {
      estadoSeleccion.classList.remove("visible");
    }
  }

  async function refrescarEstadoSesion() {
    if (!sesionId || redirigiendo) return;

    try {
      const res = await fetch(`/sesion/${sesionId}/estado/`, {
        cache: "no-store",
        credentials: "same-origin",
      });

      if (!res.ok) return;

      const data = await res.json();

      if (timerTematica) {
        timerTematica.textContent = formatearTiempo(data.segundosRestantes);
      }

      actualizarContador(data);

      if (data.faseActual && data.faseActual !== "f2_tematicas" && data.rutaAlumno) {
        redirigiendo = true;
        window.location.href = data.rutaAlumno;
        return;
      }

      const miGrupo = (data.grupos || []).find((grupo) => Number(grupo.id) === Number(grupoId));

      if (miGrupo && miGrupo.listoF2 && !bloqueado) {
        aplicarModoBloqueado(
          miGrupo.desafioIdExterno,
          miGrupo.desafioNombre,
          miGrupo.desafioDescripcion
        );
      }
    } catch (error) {
      console.error("Error consultando estado de sesión:", error);
    }
  }

  if (desafioConfirmado) {
    aplicarModoBloqueado(
      desafioIdActual,
      desafioNombreActual,
      desafioDescripcionActual
    );
  } else {
    aplicarTextoBotones();
  }

  botones.forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (enviando || bloqueado) return;

      const desafioId = btn.dataset.desafioId;
      const card = btn.closest(".challenge-card");

      if (!desafioId || !card) return;

      const nombre = card.dataset.title || "";
      const descripcion = card.dataset.desc || "";

      if (!confirm(textoConfirmarDesafio(nombre))) {
        return;
      }

      enviando = true;
      mostrarError("");

      botones.forEach((boton) => {
        boton.disabled = true;
      });

      try {
        const res = await fetch(guardarDesafioUrl, {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
            "X-Requested-With": "XMLHttpRequest",
          },
          body: JSON.stringify({
            desafio_id: desafioId,
          }),
          cache: "no-store",
        });

        const data = await res.json();

        if (!res.ok || !data.ok) {
          throw new Error(data.error || tJuego("desafios_error_guardar", "No se pudo guardar el desafío."));
        }

        aplicarModoBloqueado(
          data.desafio_id,
          data.desafio_nombre,
          data.desafio_descripcion
        );

        await refrescarEstadoSesion();
      } catch (error) {
        console.error("Error guardando desafío:", error);

        mostrarError(
          error.message ||
          tJuego("desafios_error_guardar_generico", "Hubo un problema al guardar el desafío.")
        );

        aplicarModoEditable();
      } finally {
        enviando = false;
      }
    });
  });

  window.addEventListener("idiomaJuegoCambiado", () => {
    aplicarTextoBotones();

    if (contador) {
      contador.textContent = textoGruposListos(ultimoListos, ultimoTotal);
    }
  });

  refrescarEstadoSesion();
  setInterval(refrescarEstadoSesion, 1000);
});