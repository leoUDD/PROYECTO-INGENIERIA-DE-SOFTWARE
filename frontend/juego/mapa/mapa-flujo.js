if (exigirSesionGrupo()) {
  const boton = document.getElementById("bt-btn");
  let enviado = false;

  async function confirmarMapa(evento) {
    evento?.preventDefault();

    if (!boton || enviado) {
      return;
    }

    enviado = true;
    boton.style.pointerEvents = "none";
    boton.textContent = "▶ ESPERANDO A LOS EQUIPOS...";

    try {
      const estado = await llamarApiJuego(
        "/api/fase2/listo",
        {
          method: "POST",
          body: JSON.stringify({
            etapa: "mapa_empatia",
          }),
        },
      );

      redirigirEstadoFase2(
        estado,
        ["habilidades.html"],
      );
    } catch (error) {
      enviado = false;
      boton.style.pointerEvents = "";
      boton.textContent = "▶ CONTINUAR A DESAFÍOS";
      mostrarErrorJuego(error);
    }
  }

  boton?.addEventListener(
    "click",
    confirmarMapa,
    true,
  );

  crearPollingFase2((estado) => {
    const progreso = estado.progreso?.mapaEmpatia;

    if (estado.grupo?.listoF2Mapa && boton) {
      enviado = true;
      boton.style.pointerEvents = "none";
      boton.textContent =
        progreso
          ? `▶ ESPERANDO A LOS EQUIPOS (${progreso.completados}/${progreso.totalGrupos})`
          : "▶ ESPERANDO A LOS EQUIPOS...";
    }

    redirigirEstadoFase2(
      estado,
      ["habilidades.html"],
    );
  });
}
