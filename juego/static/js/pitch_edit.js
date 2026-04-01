(function () {
  const textarea = document.getElementById("pitch-text");
  const btnLimpiar = document.getElementById("btnLimpiar");
  const hint = document.getElementById("saveHint");

  if (!textarea) return;

  let saveTimer = null;
  let debounceTimer = null;
  let ultimoTextoGuardado = textarea.value || "";

  function setHint(texto) {
    if (!hint) return;
    hint.textContent = texto;
  }

  async function guardarEnBackend(texto) {
    const res = await fetch(GUARDAR_PITCH_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": CSRF_TOKEN,
      },
      body: JSON.stringify({
        pitch_texto: texto,
      }),
    });

    const data = await res.json();

    if (!res.ok || !data.ok) {
      throw new Error(data.error || "No se pudo guardar el pitch.");
    }

    ultimoTextoGuardado = texto;
    setHint("Guardado automáticamente.");
  }

  function programarGuardado() {
    const textoActual = textarea.value;

    setHint("Guardando...");

    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(async () => {
      try {
        await guardarEnBackend(textoActual);
        clearTimeout(saveTimer);
        saveTimer = setTimeout(() => {
          setHint("Los cambios se guardan automáticamente.");
        }, 1000);
      } catch (error) {
        console.error("Error guardando pitch:", error);
        setHint("Error al guardar. Intenta nuevamente.");
      }
    }, 500);
  }

  textarea.addEventListener("input", () => {
    if (textarea.value === ultimoTextoGuardado) return;
    programarGuardado();
  });

  btnLimpiar?.addEventListener("click", () => {
    setHint("Borrando contenido...");
  });
})();