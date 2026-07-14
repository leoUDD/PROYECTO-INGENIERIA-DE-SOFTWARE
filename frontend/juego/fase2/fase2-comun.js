function rutaActualFase2() {
  return window.location.pathname.split("/").pop() || "";
}

async function obtenerEstadoFase2() {
  return llamarApiJuego("/api/fase2/estado");
}

function formatearTimerFase2(segundos) {
  const total = Math.max(0, Number(segundos || 0));
  const minutos = Math.floor(total / 60);
  const resto = total % 60;
  return `${String(minutos).padStart(2, "0")}:${String(resto).padStart(2, "0")}`;
}

function actualizarTimerFase2(elemento, segundos) {
  if (elemento) elemento.textContent = formatearTimerFase2(segundos);
}

function esRutaPermitidaFase2(ruta, permitidas) {
  return permitidas.includes(ruta);
}

function redirigirEstadoFase2(estado, permitidas = []) {
  const sugerida = String(estado?.rutaSugerida || "");
  const actual = rutaActualFase2();
  const nombreSugerido = sugerida.split("/").pop() || "";

  if (!sugerida || nombreSugerido === actual) return false;

  // Permite navegar entre páginas de una misma etapa, por ejemplo
  // Temáticas y Desafíos, pero no bloquea un cambio real de fase.
  if (
    esRutaPermitidaFase2(actual, permitidas) &&
    esRutaPermitidaFase2(nombreSugerido, permitidas)
  ) {
    return false;
  }

  window.location.replace(sugerida);
  return true;
}

function renderProgresoFase2(elemento, progreso) {
  if (!elemento || !progreso) return;
  elemento.textContent = `${progreso.completados}/${progreso.totalGrupos} grupos listos`;
}

function crearPollingFase2(callback, intervalo = 3000) {
  let activo = true;
  let ejecutando = false;

  async function ciclo() {
    if (!activo || ejecutando) return;
    ejecutando = true;
    try {
      const estado = await obtenerEstadoFase2();
      await callback(estado);
    } catch (error) {
      mostrarErrorJuego(error);
    } finally {
      ejecutando = false;
    }
  }

  ciclo();
  const id = setInterval(ciclo, intervalo);

  window.addEventListener("beforeunload", () => {
    activo = false;
    clearInterval(id);
  });

  return () => {
    activo = false;
    clearInterval(id);
  };
}

function escaparHtmlFase2(valor) {
  return String(valor ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
