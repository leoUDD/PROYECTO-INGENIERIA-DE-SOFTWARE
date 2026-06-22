document.addEventListener("DOMContentLoaded", () => {
  const pageData = document.body.dataset;
  const sesionId = pageData.sesionId || "";
  const grupoId = pageData.grupoId || "";
  const csrfToken = pageData.csrfToken || "";
  const guardarPitchUrl = pageData.guardarPitchUrl || "";

  const boton = document.getElementById("btn-listo-fase");
  const textoEspera = document.getElementById("texto-espera-fase");
  const contador = document.getElementById("contador-listos-fase");
  const timerContainer = document.getElementById("timer-wrap-pitch");
  const timerElement = document.getElementById("timer");
  const alarmAudio = document.getElementById("alarm-audio");
  const overlay = document.getElementById("inicio-fase-overlay");
  const textarea = document.getElementById("pitch-text");
  const desafioToggle = document.getElementById("desafioToggle");
  const desafioBody = document.getElementById("desafioBody");
  const desafioIcono = document.getElementById("desafioIcono");
  const astroTriggerPitch = document.getElementById("astroTriggerPitch");
  const astroPitchOverlay = document.getElementById("astroPitchOverlay");
  const astroPitchTitulo = document.getElementById("astroPitchTitulo");
  const astroPitchMensaje = document.getElementById("astroPitchMensaje");
  const astroPitchCerrar = document.getElementById("astroPitchCerrar");

  const blurTargets = [
    document.getElementById("tituloPitch"),
    document.getElementById("subtituloPitch"),
    document.getElementById("timer-wrap-pitch"),
    document.getElementById("desafioPitchWrap"),
    document.getElementById("tipsPitch"),
    document.getElementById("pitchFormWrap"),
  ];

  let guardarPitchTimeout = null;
  let timeLeft = 0;
  let timerInterval = null;
  let timerStarted = false;
  let redirigiendo = false;
  let countdownMostrado = false;
  let countdownEnCurso = false;
  let timerRealSolicitado = false;
  let astroInicioMostrado = false;
  let astroMitadMostrado = false;
  let astroActivo = false;
  let astroModo = "inicio";

  function tJuego(clave, fallback = "") {
    const idioma = window.i18nJuego?.obtenerIdioma?.() || "es";
    return window.i18nJuego?.traducciones?.[idioma]?.[clave] || fallback;
  }

  function textoGruposListos(listos, total) { return `${listos}/${total} ${tJuego("pitch_grupos_listos", "grupos listos")}`; }
  function textoBotonListo()      { return tJuego("pitch_boton_listo", "⚡ Listo para comenzar"); }
  function textoEsperando()       { return tJuego("pitch_boton_esperando", "Esperando..."); }
  function textoEsperandoEquipos(){ return tJuego("pitch_esperando_equipos", "Esperando a los demás equipos..."); }

  function aplicarTraduccionDinamicaPitch() {
    if (boton) boton.textContent = boton.disabled ? textoEsperando() : textoBotonListo();
    if (textoEspera) textoEspera.textContent = textoEsperandoEquipos();
    if (contador) {
      const match = (contador.textContent || "").match(/(\d+)\/(\d+)/);
      if (match) contador.textContent = textoGruposListos(match[1], match[2]);
    }
  }

  function actualizarBadgeDesafio(data) {
    const miGrupo = (data.grupos || []).find(g => Number(g.id) === Number(grupoId));
    if (!miGrupo) return;
    const titulo = miGrupo.desafioNombre || tJuego("pitch_desafio_no_seleccionado", "Desafío no seleccionado");
    const descripcion = miGrupo.desafioDescripcion || tJuego("pitch_desafio_sin_descripcion", "Aún no hay descripción disponible.");
    const desafioNombre = document.getElementById("desafioNombre");
    const desafioDescripcion = document.getElementById("desafioDescripcion");
    if (desafioNombre) desafioNombre.textContent = titulo;
    if (desafioDescripcion) desafioDescripcion.textContent = descripcion;
  }

  function abrirAstroPitch(titulo, mensaje) {
    if (!astroPitchOverlay) return;
    if (astroPitchTitulo) astroPitchTitulo.textContent = titulo;
    if (astroPitchMensaje) astroPitchMensaje.textContent = mensaje;
    astroPitchOverlay.classList.add("visible");
    astroPitchOverlay.setAttribute("aria-hidden", "false");
  }

  function cerrarAstroPitch() {
    if (!astroPitchOverlay) return;
    astroPitchOverlay.classList.remove("visible");
    astroPitchOverlay.setAttribute("aria-hidden", "true");
    astroActivo = false;
  }

  function analizarPitchActual() {
    const texto = (textarea?.value || "").trim();
    const palabras = texto.split(/\s+/).filter(Boolean).length;
    if (palabras < 20) return tJuego("pitch_astro_corto", "Tu pitch aún está muy corto. Agrega el problema, la solución y por qué tu idea aporta valor.");
    if (palabras < 45) return tJuego("pitch_astro_medio", "Vas bien. Ahora intenta explicar mejor el beneficio de tu solución y cómo ayuda a la persona del desafío.");
    return tJuego("pitch_astro_bueno", "Buen avance. Revisa que tu pitch tenga problema, solución, valor diferencial y un cierre claro.");
  }

  function mostrarAstroFlotando(modo) {
    if (!astroTriggerPitch) return;
    astroModo = modo; astroActivo = false;
    astroTriggerPitch.classList.remove("oculto");
    astroTriggerPitch.classList.add("visible");
  }

  function ocultarAstroFlotando() {
    if (!astroTriggerPitch) return;
    astroTriggerPitch.classList.remove("visible");
    astroTriggerPitch.classList.add("oculto");
  }

  function abrirAstroPitchInteractivo() {
    if (astroActivo) return;
    astroActivo = true;
    ocultarAstroFlotando();
    if (astroModo === "inicio") {
      abrirAstroPitch(
        tJuego("pitch_astro_titulo_inicio", "Estructura recomendada"),
        tJuego("pitch_astro_mensaje_inicio", "Usen esta estructura: Problema -> Solución -> Beneficio o valor -> Cierre convincente. No intenten decirlo todo: sean claros y directos.")
      );
    } else {
      abrirAstroPitch(tJuego("pitch_astro_titulo_mitad", "Mitad del tiempo"), analizarPitchActual());
    }
  }

  async function guardarPitch() {
    if (!textarea || !guardarPitchUrl) return;
    try {
      await fetch(guardarPitchUrl, {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
        body: JSON.stringify({ pitch: textarea.value || "" })
      });
    } catch (error) { console.error("Error guardando pitch:", error); }
  }

  textarea?.addEventListener("input", () => {
    clearTimeout(guardarPitchTimeout);
    guardarPitchTimeout = setTimeout(() => guardarPitch(), 700);
  });
  textarea?.addEventListener("blur", guardarPitch);

  desafioToggle?.addEventListener("click", () => {
    const abierto = !desafioBody.hasAttribute("hidden");
    if (abierto) { desafioBody.setAttribute("hidden", ""); if (desafioIcono) desafioIcono.textContent = "▼"; }
    else          { desafioBody.removeAttribute("hidden");  if (desafioIcono) desafioIcono.textContent = "▲"; }
  });

  astroTriggerPitch?.addEventListener("click", abrirAstroPitchInteractivo);
  astroPitchCerrar?.addEventListener("click", cerrarAstroPitch);
  astroPitchOverlay?.addEventListener("click", (e) => { if (e.target === astroPitchOverlay) cerrarAstroPitch(); });

  function activarFase() {
    blurTargets.forEach(el => { if (!el) return; el.classList.remove("blur-target-bloqueado", "timer-esperando"); el.classList.add("blur-target-activo"); });
    if (timerContainer) timerContainer.classList.remove("timer-esperando");
    if (overlay) overlay.classList.add("overlay-hidden");
    if (!astroInicioMostrado) { astroInicioMostrado = true; setTimeout(() => mostrarAstroFlotando("inicio"), 700); }
  }

  function bloquearFase() {
    blurTargets.forEach(el => { if (!el) return; el.classList.remove("blur-target-activo"); el.classList.add("blur-target-bloqueado"); });
    if (timerContainer) timerContainer.classList.add("timer-esperando");
    if (overlay) overlay.classList.remove("overlay-hidden");
    ocultarAstroFlotando();
    cerrarAstroPitch();
  }

  function renderTimer() {
    const min = Math.floor(Math.max(0, timeLeft) / 60);
    const sec = Math.max(0, timeLeft) % 60;
    if (timerElement) timerElement.textContent = `${min.toString().padStart(2,"0")}:${sec.toString().padStart(2,"0")}`;
  }

  function startTimer() {
    if (timerInterval) return;
    timerInterval = setInterval(() => {
      timeLeft--;
      renderTimer();
      if (timeLeft <= 0) { clearInterval(timerInterval); timerInterval = null; alarmAudio?.play().catch(() => {}); }
    }, 1000);
  }

  async function iniciarTimerRealDespuesCountdown() {
    if (timerRealSolicitado) return;
    timerRealSolicitado = true;
    try {
      const res = await fetch(`/sesion/${sesionId}/iniciar-timer-inicio-fase/`, {
        method: "POST", credentials: "same-origin",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
        body: JSON.stringify({ fase: "f4_construccion_pitch" })
      });
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error(data.error || "Error timer");
      const bs = Number(data.segundosRestantes);
      if (!Number.isNaN(bs)) { timeLeft = bs; renderTimer(); }
    } catch (err) { console.error("Error iniciando timer pitch:", err); timerRealSolicitado = false; }
  }

  async function syncTimer() {
    try {
      const res = await fetch(`/sesion/${sesionId}/estado/`, { cache: "no-store", credentials: "same-origin" });
      if (!res.ok) return;
      const data = await res.json();
      actualizarBadgeDesafio(data);

      if (contador) {
        const total =
          data.totalListosInicio ??
          data.totalGrupos ??
          (Array.isArray(data.grupos) ? data.grupos.length : 0);

        const listos =
          data.listosInicio ??
          data.gruposListosF4 ??
          (Array.isArray(data.grupos) ? data.grupos.filter(g => g.listoF4).length : 0);

        contador.textContent = textoGruposListos(listos, total);
      }

      const miGrupo = (data.grupos || []).find(g => Number(g.id) === Number(grupoId));
      if (miGrupo?.listoF4) { boton.disabled = true; boton.textContent = textoEsperando(); }

      if (data.faseActual && data.faseActual !== "f4_construccion_pitch") {
        if (data.rutaAlumno && window.location.pathname !== data.rutaAlumno && !redirigiendo) { redirigiendo = true; window.location.href = data.rutaAlumno; }
        return;
      }

      if (data.inicioFaseHabilitado) {
        if (!countdownMostrado && !countdownEnCurso) {
          countdownEnCurso = true;
          window.oaiCountdown.run(async () => {
            countdownMostrado = true; countdownEnCurso = false;
            await iniciarTimerRealDespuesCountdown();
            activarFase();
          });
          return;
        }
        if (countdownMostrado && !countdownEnCurso) activarFase();
      } else {
        countdownMostrado = false; countdownEnCurso = false;
        timerRealSolicitado = false; astroInicioMostrado = false; astroMitadMostrado = false;
        bloquearFase();
      }

      const backendTime = Number(data.segundosRestantes);

      if (!astroMitadMostrado && timerStarted && Number(timeLeft) <= 150) {
        astroMitadMostrado = true;
        mostrarAstroFlotando("mitad");
      }

      if (!timerStarted) { timeLeft = backendTime; renderTimer(); }

      if (!timerStarted && data.timerCorriendo && data.inicioFaseHabilitado) {
        if (!countdownMostrado || countdownEnCurso) return;
        timerStarted = true; timeLeft = backendTime; renderTimer(); startTimer(); return;
      }

      if (timerStarted && !data.timerCorriendo) {
        clearInterval(timerInterval); timerInterval = null;
        timeLeft = backendTime; renderTimer(); timerStarted = false;
      }
    } catch (e) { console.error("Error timer pitch:", e); }
  }

  boton?.addEventListener("click", async () => {
    boton.disabled = true; boton.textContent = textoEsperando();
    try {
      const res = await fetch(`/grupo/${grupoId}/listo/`, {
        method: "POST", credentials: "same-origin",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
        body: JSON.stringify({ fase: "f4" })
      });
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error(data.error || tJuego("pitch_error_listo", "No se pudo marcar listo."));
      syncTimer();
    } catch (err) {
      console.error("Error marcando listo pitch:", err);
      boton.disabled = false; boton.textContent = textoBotonListo();
      if (textoEspera) textoEspera.textContent = tJuego("pitch_error_registro", "No se pudo registrar. Intenta nuevamente.");
    }
  });

  window.addEventListener("idiomaJuegoCambiado", () => aplicarTraduccionDinamicaPitch());

  bloquearFase();
  renderTimer();
  aplicarTraduccionDinamicaPitch();
  setInterval(syncTimer, 1000);
  syncTimer();
});