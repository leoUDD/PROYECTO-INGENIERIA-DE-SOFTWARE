document.addEventListener("DOMContentLoaded", () => {
  const pageData = document.body.dataset;
  const sesionId = pageData.sesionId || "";
  const grupoId = pageData.grupoId || "";
  const csrfToken = pageData.csrfToken || "";
  const presentarPitchUrl = pageData.presentarPitchUrl || "";

  const btnOrdenListo = document.getElementById("btnOrdenListo");
  const ordenListoEstado = document.getElementById("ordenListoEstado");
  const accionesListoOrden = document.getElementById("accionesListoOrden");
  const varitasEl = document.getElementById("varitas");
  const chispasEl = document.getElementById("chispas");
  const estadoAnimacionSorteo = document.getElementById("estadoAnimacionSorteo");
  const dotsSorteo = document.getElementById("dotsSorteo");
  const listaOrdenBonita = document.getElementById("listaOrdenBonita");
  const flashSorteo = document.getElementById("flashSorteo");
  const sorteoStage = document.getElementById("sorteoStage");
  const resultadoStage = document.getElementById("resultadoStage");
  const audioSorteoAgitar = document.getElementById("audioSorteoAgitar");
  const audioSorteoReveal = document.getElementById("audioSorteoReveal");

  let ordenSorteadoPrevio = false;
  let animacionActiva = false;
  let ultimoOrdenRenderizado = "";

  function tOrden(clave, fallback) {
    try {
      const idioma = window.i18nJuego?.obtenerIdioma?.() || "es";
      return window.i18nJuego?.traducciones?.[idioma]?.[clave] || fallback;
    } catch (error) {
      return fallback;
    }
  }

  function reproducirAudio(el) {
    if (!el) return;
    try {
      el.currentTime = 0;
      el.play().catch(() => {});
    } catch (error) {}
  }

  function setDots(activo) {
    if (!dotsSorteo) return;
    const dots = dotsSorteo.querySelectorAll(".dot");
    dots.forEach((dot, i) => {
      dot.classList.toggle("active", i === activo);
    });
  }

  function mostrarSoloAnimacion() {
    if (sorteoStage) sorteoStage.classList.remove("oculto");
    if (resultadoStage) resultadoStage.classList.add("oculto");
  }

  function mostrarSoloResultado() {
    if (sorteoStage) sorteoStage.classList.add("oculto");
    if (resultadoStage) resultadoStage.classList.remove("oculto");
  }

  function resetVisualSorteo() {
    if (varitasEl) {
      varitasEl.classList.remove("sorteando");
      varitasEl.querySelectorAll(".varita").forEach((v) => v.classList.remove("ganadora"));
    }

    if (chispasEl) chispasEl.classList.remove("visible");
    if (flashSorteo) flashSorteo.classList.remove("visible");
    if (listaOrdenBonita) listaOrdenBonita.innerHTML = "";

    if (estadoAnimacionSorteo) {
      estadoAnimacionSorteo.textContent = tOrden("orden_presentacion_esperando", "Esperando el sorteo");
    }

    setDots(0);
    ultimoOrdenRenderizado = "";
    mostrarSoloAnimacion();
  }

  function serializarOrden(ordenPitch, grupoActual) {
    return JSON.stringify({
      ordenPitch: ordenPitch || [],
      grupoActualId: grupoActual ? Number(grupoActual.id) : null,
    });
  }

  function renderOrdenBonito(ordenPitch, grupoActual) {
    if (!listaOrdenBonita) return;

    const firma = serializarOrden(ordenPitch, grupoActual);
    if (firma === ultimoOrdenRenderizado) return;

    listaOrdenBonita.innerHTML = (ordenPitch || []).map((item) => {
      const esActual = grupoActual && Number(grupoActual.id) === Number(item.id);

      return `
        <div class="fila-orden">
          <div class="numero-orden">${item.orden}</div>
          <div class="nombre-orden">${item.nombre}</div>
          ${esActual ? `<div class="primero-tag">${tOrden("orden_presentacion_primero_tag", "primer turno")}</div>` : ""}
        </div>
      `;
    }).join("");

    ultimoOrdenRenderizado = firma;
  }

  function elegirVaritaGanadora() {
    return 2;
  }

  function mostrarAnimacionSorteo(ordenPitch, grupoActual) {
    if (animacionActiva) return;
    animacionActiva = true;

    mostrarSoloAnimacion();

    if (listaOrdenBonita) listaOrdenBonita.innerHTML = "";

    if (estadoAnimacionSorteo) {
      estadoAnimacionSorteo.textContent = tOrden("orden_presentacion_sorteando", "Sorteando...");
    }

    setDots(1);

    if (varitasEl) {
      varitasEl.classList.add("sorteando");
      varitasEl.querySelectorAll(".varita").forEach((v) => v.classList.remove("ganadora"));
    }

    reproducirAudio(audioSorteoAgitar);

    setTimeout(() => {
      if (estadoAnimacionSorteo) {
        estadoAnimacionSorteo.textContent = tOrden("orden_presentacion_primero", "Y el primero es...");
      }

      if (chispasEl) chispasEl.classList.add("visible");

      const indiceGanador = elegirVaritaGanadora(ordenPitch);
      const varitas = varitasEl ? varitasEl.querySelectorAll(".varita") : [];

      if (varitas[indiceGanador]) {
        varitas[indiceGanador].classList.add("ganadora");
      }

      setDots(2);
    }, 1500);

    setTimeout(() => {
      if (flashSorteo) flashSorteo.classList.add("visible");
      reproducirAudio(audioSorteoReveal);
    }, 2400);

    setTimeout(() => {
      if (varitasEl) varitasEl.classList.remove("sorteando");
    }, 3000);

    setTimeout(() => {
      if (flashSorteo) flashSorteo.classList.remove("visible");
      renderOrdenBonito(ordenPitch, grupoActual);
      mostrarSoloResultado();
      animacionActiva = false;
    }, 3550);
  }

  function renderEstadoFase(data) {
    const estado = document.getElementById("estadoFaseTexto");
    if (!estado) return;

    if (data.faseActual === "f4_orden_pitch") {
      if (!data.ordenSorteado) {
        estado.textContent = tOrden(
          "orden_presentacion_info_pre_sorteo",
          "Cuando todos los equipos estén listos, se realizará el sorteo del orden de presentación."
        );
      } else {
        estado.textContent = tOrden(
          "orden_presentacion_info_sorteado",
          "El orden ya fue sorteado. Cuando todos los equipos estén listos nuevamente, comenzará la ronda de presentaciones."
        );
      }

      if (accionesListoOrden) accionesListoOrden.style.display = "flex";

      if (ordenListoEstado) {
        ordenListoEstado.textContent = `${data.gruposListosF4Orden || 0}/${data.totalGrupos || 0} ${tOrden("orden_presentacion_grupos_listos", "grupos listos")}`;
      }

      const miGrupo = (data.grupos || []).find((g) => Number(g.id) === Number(grupoId));
      const yaListo = miGrupo?.listoF4Orden;

      if (btnOrdenListo) {
        btnOrdenListo.disabled = !!yaListo;
        btnOrdenListo.textContent = yaListo
          ? tOrden("orden_presentacion_boton_listo", "Listo ✓")
          : tOrden("orden_presentacion_boton", "¡Estoy listo!");
      }
    } else if (data.faseActual === "f4_presentacion_pitch") {
      estado.textContent = tOrden("orden_presentacion_info_presentacion", "La presentación ha comenzado.");
      if (accionesListoOrden) accionesListoOrden.style.display = "none";
    } else {
      estado.textContent = "";
      if (accionesListoOrden) accionesListoOrden.style.display = "none";
    }
  }

  async function marcarListoOrden() {
    try {
      const resp = await fetch(`/grupo/${grupoId}/listo/`, {
        method: "POST",
        headers: {
          "X-CSRFToken": csrfToken,
          "Content-Type": "application/json",
        },
        credentials: "same-origin",
        body: JSON.stringify({}),
      });

      const data = await resp.json();

      if (!resp.ok || !data.ok) {
        console.error("Error al marcar listo:", data);
        return;
      }

      await cargarOrden();
    } catch (error) {
      console.error("Error marcando listo en orden:", error);
    }
  }

  async function cargarOrden() {
    if (!sesionId || !grupoId) return;

    try {
      const res = await fetch(`/sesion/${sesionId}/estado-presentacion/`, {
        credentials: "same-origin",
        cache: "no-store",
      });

      const data = await res.json();

      if (!res.ok || !data.ok) return;

      if (data.faseActual === "f4_presentacion_pitch") {
        if (presentarPitchUrl) window.location.replace(presentarPitchUrl);
        return;
      }

      if (data.faseActual && data.faseActual !== "f4_orden_pitch") {
        if (data.rutaAlumno) {
          window.location.replace(data.rutaAlumno);
          return;
        }
      }

      if (!data.ordenSorteado) {
        resetVisualSorteo();
        ordenSorteadoPrevio = false;
      }

      if (data.ordenSorteado && !ordenSorteadoPrevio && data.ordenPitch && data.ordenPitch.length) {
        ordenSorteadoPrevio = true;
        mostrarAnimacionSorteo(data.ordenPitch, data.grupoActual);
        renderEstadoFase(data);
        return;
      }

      ordenSorteadoPrevio = !!data.ordenSorteado;

      if (data.ordenSorteado && data.ordenPitch && data.ordenPitch.length && !animacionActiva) {
        renderOrdenBonito(data.ordenPitch, data.grupoActual);
        mostrarSoloResultado();
      }

      renderEstadoFase(data);
    } catch (error) {
      console.error("Error cargando orden:", error);
    }
  }

  if (btnOrdenListo) {
    btnOrdenListo.addEventListener("click", marcarListoOrden);
  }

  window.addEventListener("idiomaJuegoCambiado", () => cargarOrden());

  cargarOrden();
  setInterval(cargarOrden, 1500);
});
