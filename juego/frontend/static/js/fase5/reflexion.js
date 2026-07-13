function tReflexion(clave, fallback) {
      try {
        const idioma = window.i18nJuego?.obtenerIdioma?.() || "es";
        return window.i18nJuego?.traducciones?.[idioma]?.[clave] || fallback;
      } catch (e) { return fallback; }
    }

    function aplicarTextosReflexion() {
      document.title = tReflexion("reflexion_document_title", "Misión Emprende UDD — Reflexión Final");

      const cardReflexion = document.getElementById("cardReflexion");
      if (cardReflexion) cardReflexion.setAttribute("aria-label", tReflexion("reflexion_aria_card", "Reflexión final"));

      const qrGrid = document.getElementById("qrGrid");
      if (qrGrid) qrGrid.setAttribute("aria-label", tReflexion("reflexion_aria_qr", "Códigos QR finales"));

      const qrInstagramImg = document.getElementById("qrInstagramImg");
      if (qrInstagramImg) qrInstagramImg.alt = tReflexion("reflexion_instagram_alt", "Código QR Instagram Misión Emprende");

      const qrEvaluacionImg = document.getElementById("qrEvaluacionImg");
      if (qrEvaluacionImg) qrEvaluacionImg.alt = tReflexion("reflexion_evaluacion_alt", "Código QR Evaluación de la actividad");
    }

    document.addEventListener("DOMContentLoaded", aplicarTextosReflexion);
    window.addEventListener("idiomaJuegoCambiado", aplicarTextosReflexion);

/* ── PERSONAJES CLICKEABLES ── */
    (function () {
      const personajes = [
        { id: "per3", bocId: "bocPer3", clave: "reflexion_per3_msg", fallback: "¡Fue un honor misionar con ustedes, agentes!" },
        { id: "per4", bocId: "bocPer4", clave: "reflexion_per4_msg", fallback: "¡El trabajo en equipo los llevó hasta aquí. ¡Bien hecho!" },
        { id: "per5", bocId: "bocPer5", clave: "reflexion_per5_msg", fallback: "La próxima misión nos espera. ¡Prepárense!" },
        { id: "per6", bocId: "bocPer6", clave: "reflexion_per6_msg", fallback: "Recuerden: creatividad, empatía y comunicación." },
      ];

      function tJuego(clave, fallback) {
        try { const i = window.i18nJuego?.obtenerIdioma?.() || "es"; return window.i18nJuego?.traducciones?.[i]?.[clave] || fallback; }
        catch(e) { return fallback; }
      }

      function cerrarTodos() {
        document.querySelectorAll(".astro-bocadillo").forEach(b => b.classList.remove("visible"));
      }
      window._cerrarBocadillos = cerrarTodos;

      personajes.forEach(({ id, bocId, clave, fallback }) => {
        const btn = document.getElementById(id);
        const boc = document.getElementById(bocId);
        if (!btn || !boc) return;

        let timer = null;

        btn.addEventListener("click", (e) => {
          e.stopPropagation();
          const yaVisible = boc.classList.contains("visible");
          cerrarTodos();
          if (!yaVisible) {
            boc.textContent = tJuego(clave, fallback);
            boc.classList.add("visible");
            clearTimeout(timer);
            timer = setTimeout(() => boc.classList.remove("visible"), 4000);
          }
        });
      });

      document.addEventListener("click", cerrarTodos);
    })();

    /* ── ASTRONAUTA ── */
    (function () {
      const btn       = document.getElementById("astroReflexion");
      const bocadillo = document.getElementById("astroBocadillo");
      if (!btn || !bocadillo) return;

      let visible = false;
      let timer   = null;

      function tJuego(clave, fallback) {
        try {
          const idioma = window.i18nJuego?.obtenerIdioma?.() || "es";
          return window.i18nJuego?.traducciones?.[idioma]?.[clave] || fallback;
        } catch(e) { return fallback; }
      }

      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const yaVisible = bocadillo.classList.contains("visible");
        if (window._cerrarBocadillos) window._cerrarBocadillos();

        bocadillo.textContent = tJuego(
          "reflexion_astro_mensaje",
          "Gracias por jugar, agente. ¡Hasta la próxima misión!"
        );

        if (!yaVisible) {
          bocadillo.classList.add("visible");
          visible = true;
        }

        clearTimeout(timer);
        if (!yaVisible) {
          timer = setTimeout(() => {
            bocadillo.classList.remove("visible");
            visible = false;
          }, 4000);
        } else {
          visible = false;
        }
      });

      document.addEventListener("click", (e) => {
        if (e.target !== btn && !btn.contains(e.target)) {
          bocadillo.classList.remove("visible");
          visible = false;
          clearTimeout(timer);
        }
      });
    })();

    /* ── CONFETI ── */
    (function () {
      const canvas = document.getElementById("confeti-canvas");
      const ctx    = canvas.getContext("2d");
      const cols   = ["#00C8FF","#FF7A1A","#FFD700","#FF4D8F","#7C3AED","#22C55E","#fff","#f9a8d4"];

      function resize() { canvas.width = innerWidth; canvas.height = innerHeight; }
      resize();
      window.addEventListener("resize", resize);

      let piezas = [];
      function nuevaPieza(y) {
        return {
          x: Math.random() * canvas.width,
          y: y ?? -14,
          w: Math.random() * 11 + 5,
          h: Math.random() * 6 + 3,
          color: cols[Math.floor(Math.random() * cols.length)],
          vx: (Math.random() - .5) * 2.4,
          vy: Math.random() * 2.6 + 1.1,
          rot: Math.random() * Math.PI * 2,
          drot: (Math.random() - .5) * .13,
        };
      }

      for (let i = 0; i < 130; i++) piezas.push(nuevaPieza(Math.random() * innerHeight));

      (function loop() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        if (piezas.length < 100) piezas.push(nuevaPieza());
        piezas = piezas.filter(p => {
          p.x += p.vx; p.y += p.vy; p.rot += p.drot;
          if (p.y > canvas.height + 20) return false;
          ctx.save();
          ctx.translate(p.x, p.y);
          ctx.rotate(p.rot);
          ctx.fillStyle = p.color;
          ctx.fillRect(-p.w/2, -p.h/2, p.w, p.h);
          ctx.restore();
          return true;
        });
        requestAnimationFrame(loop);
      })();
    })();

    /* ── MÚSICA ── */
    (function () {
      const audio = document.getElementById("musica-reflexion");
      const btn   = document.getElementById("btn-musica-reflexion");
      if (!audio) return;
      audio.volume = 0.32;

      function arrancar() {
        audio.play().catch(() => {});
        document.removeEventListener("click",      arrancar);
        document.removeEventListener("touchstart", arrancar);
      }
      document.addEventListener("click",      arrancar);
      document.addEventListener("touchstart", arrancar);

      document.addEventListener("visibilitychange", () => {
        if (document.hidden) audio.pause();
        else if (!audio.muted) audio.play().catch(() => {});
      });

      window.toggleMusicaReflexion = function () {
        audio.muted   = !audio.muted;
        if (btn) {
          btn.innerHTML = audio.muted ? "&#128263;" : "&#128266;";
          btn.title     = audio.muted ? "Activar música" : "Silenciar música";
          btn.setAttribute("aria-label", btn.title);
        }
      };

      if (btn) {
        btn.addEventListener("click", window.toggleMusicaReflexion);
      }

      window.addEventListener("beforeunload", () => audio.pause());
    })();