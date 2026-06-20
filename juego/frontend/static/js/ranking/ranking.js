/* ══════════════════════════════════
       MÚSICA DE FONDO (sin cambios)
    ══════════════════════════════════ */
    (function () {
      const audio = document.getElementById("musica-ranking");
      const btn   = document.getElementById("btn-musica-ranking");
      if (!audio) return;
      audio.volume = 0.4;
      function arrancar() {
        audio.play().catch(() => {});
        document.removeEventListener("click",      arrancar);
        document.removeEventListener("touchstart", arrancar);
      }
      document.addEventListener("click",      arrancar);
      document.addEventListener("touchstart", arrancar);
      document.addEventListener("visibilitychange", () => {
        if (document.hidden) { audio.pause(); }
        else if (!audio.muted) { audio.play().catch(() => {}); }
      });
      window.toggleMusicaRanking = function () {
        audio.muted = !audio.muted;
        if (btn) {
          btn.textContent = audio.muted ? "\uD83D\uDD07" : "\uD83D\uDD0A";
          btn.title = audio.muted ? "Activar música" : "Silenciar música";
          btn.setAttribute("aria-label", btn.title);
        }
      };

      if (btn) {
        btn.addEventListener("click", window.toggleMusicaRanking);
      }

      window.addEventListener("beforeunload", () => audio.pause());
    })();

    /* ══════════════════════════════════
       FUEGOS ARTIFICIALES
    ══════════════════════════════════ */
    (function () {
      const canvas = document.getElementById("fw-canvas");
      if (!canvas) return;

      const ctx = canvas.getContext("2d");
      const COLORS = [
        "#00C8FF","#FF7A1A","#ffd000","#a78bfa",
        "#7dffb3","#ffffff","#ff4488","#44ffdd","#ff5533"
      ];
      let rockets = [], fwOn = false, raf = null;

      function resize() {
        canvas.width  = window.innerWidth;
        canvas.height = window.innerHeight;
      }
      resize();
      window.addEventListener("resize", resize);

      function launchRocket() {
        const x  = window.innerWidth  * (.12 + Math.random() * .76);
        const ty = window.innerHeight * (.06 + Math.random() * .38);
        rockets.push({
          x, y: window.innerHeight + 8,
          tx: x + (Math.random() - .5) * 80,
          ty, vx: 0, vy: -window.innerHeight * .02,
          color: COLORS[Math.floor(Math.random() * COLORS.length)],
          trail: [], exploded: false, parts: []
        });
      }

      function explode(r) {
        r.exploded = true;
        const n = 65 + Math.floor(Math.random() * 55);
        for (let i = 0; i < n; i++) {
          const a = Math.random() * Math.PI * 2;
          const s = 1 + Math.random() * 5.5;
          r.parts.push({
            x: r.x, y: r.y,
            vx: Math.cos(a) * s, vy: Math.sin(a) * s,
            color: r.color,
            r: 1.2 + Math.random() * 3.2,
            life: 1, decay: .009 + Math.random() * .022,
            shape: Math.random() > .5 ? "c" : "r",
            rot: Math.random() * 360, rotV: (Math.random() - .5) * 10
          });
          if (i < n * .35) {
            const c2 = COLORS[Math.floor(Math.random() * COLORS.length)];
            const s2 = .4 + Math.random() * 2.5;
            r.parts.push({
              x: r.x, y: r.y,
              vx: Math.cos(a) * s2, vy: Math.sin(a) * s2,
              color: c2, r: .8 + Math.random() * 2,
              life: 1, decay: .015 + Math.random() * .028,
              shape: "c", rot: 0, rotV: 0
            });
          }
        }
      }

      function tick() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        rockets.forEach(r => {
          if (!r.exploded) {
            r.trail.push({ x: r.x, y: r.y });
            if (r.trail.length > 18) r.trail.shift();
            r.trail.forEach((t, i) => {
              ctx.globalAlpha = (i / r.trail.length) * .55;
              ctx.fillStyle = r.color;
              ctx.beginPath();
              ctx.arc(t.x, t.y, 1.4, 0, Math.PI * 2);
              ctx.fill();
            });
            ctx.globalAlpha = 1;
            r.x += r.vx; r.y += r.vy;
            r.vx += (r.tx - r.x) * .014;
            if (r.y <= r.ty) explode(r);
          } else {
            r.parts.forEach(p => {
              if (p.life <= 0) return;
              p.x += p.vx; p.y += p.vy;
              p.vy += .065; p.vx *= .985;
              p.life -= p.decay; p.rot += p.rotV;
              ctx.save();
              ctx.globalAlpha = Math.max(0, p.life);
              ctx.fillStyle = p.color;
              ctx.translate(p.x, p.y);
              ctx.rotate(p.rot * Math.PI / 180);
              if (p.shape === "c") {
                ctx.beginPath(); ctx.arc(0, 0, p.r, 0, Math.PI * 2); ctx.fill();
              } else {
                ctx.fillRect(-p.r, -p.r * 1.7, p.r * 2, p.r * 3.4);
              }
              ctx.restore();
            });
            r.parts = r.parts.filter(p => p.life > 0);
          }
        });
        rockets = rockets.filter(r => !r.exploded || r.parts.length > 0);
        if (fwOn && Math.random() < .04) launchRocket();
        if (rockets.length > 0 || fwOn) {
          raf = requestAnimationFrame(tick);
        } else {
          ctx.clearRect(0, 0, canvas.width, canvas.height);
          raf = null;
        }
      }

      window.fwStart = function (continuous, burst) {
        fwOn = !!continuous;
        if (!raf) raf = requestAnimationFrame(tick);
        const n = burst || 5;
        for (let i = 0; i < n; i++) setTimeout(launchRocket, i * 160);
      };
      window.fwStop = function () { fwOn = false; };
    })();

    /* ══════════════════════════════════
       SUSPENSO + REVEAL (solo fase final)
    ══════════════════════════════════ */
    (function () {
      const overlay = document.getElementById("suspenseOverlay");
      if (!overlay) return;

      const bar   = document.getElementById("susBar");
      const title = document.getElementById("susTitle");
      const sub   = document.getElementById("susSub");
      const flash = document.getElementById("revealFlash");

      /* llenar barra en ~4.6 s */
      let p = 0;
      const barInt = setInterval(() => {
        p += 1; bar.style.width = p + "%";
        if (p >= 100) clearInterval(barInt);
      }, 46);

      /* revelar equipos uno a uno */
      const numTeams = document.querySelectorAll(".sus-team-row").length;
      for (let i = 0; i < numTeams; i++) {
        setTimeout(() => {
          const el = document.getElementById("susTeam" + i);
          if (el) el.classList.add("show");
        }, 600 + i * 650);
      }

      /* cambios de texto para el suspenso */
      setTimeout(() => {
        title.textContent = "Analizando datos...";
        sub.textContent   = "VERIFICANDO PUNTAJES FINALES";
      }, 1000);
      setTimeout(() => {
        title.textContent = "Identificando al ganador...";
        sub.textContent   = "RESULTADO CASI LISTO";
      }, 2800);
      setTimeout(() => {
        title.textContent    = "El ganador es...";
        sub.textContent      = "";
        title.style.fontSize = "36px";
        title.style.color    = "#00C8FF";
      }, 3800);

      /* fuegos antes del reveal */
      setTimeout(() => { if (window.fwStart) window.fwStart(false, 4); }, 3600);

      /* REVEAL */
      setTimeout(() => {
        if (window.fwStop) window.fwStop();
        flash.style.opacity = "1";
        setTimeout(() => {
          flash.style.transition = "opacity .65s";
          flash.style.opacity    = "0";
          overlay.classList.add("fade-out");
          setTimeout(() => {
            overlay.classList.add("gone");
            /* arrancar fuegos continuos */
            if (window.fwStart) window.fwStart(true, 8);
          }, 900);
        }, 130);
      }, 4800);
    })();

    /* ══════════════════════════════════
       LÓGICA ORIGINAL (sin cambios)
    ══════════════════════════════════ */
    document.addEventListener("DOMContentLoaded", () => {
      const config = document.getElementById("ranking-config");
      const faseActualEsperada = config?.dataset?.faseActual || "";
      const esRankingFinal = faseActualEsperada === "f6_ranking";
      const faseClaveRanking = esRankingFinal ? "f6" : "ranking";
      const sesionId = config?.dataset?.sesionId || "";
      const grupoId = config?.dataset?.grupoId || "";
      const csrfToken = config?.dataset?.csrfToken || "";

      const carrera         = document.getElementById("carreraWrap");
      const overlay         = document.getElementById("ganadorOverlay");
      const podio           = document.getElementById("podioWrap");
      const audio           = document.getElementById("audioCelebracion");
      const btnRankingListo = document.getElementById("btnRankingListo");
      const rankingEstado   = document.getElementById("rankingEstado");
      const btnSaltarVideo  = document.getElementById("btnSaltarVideo");

      if (btnSaltarVideo) {
        btnSaltarVideo.addEventListener("click", () => {
          if (typeof window.saltarVideo === "function") {
            window.saltarVideo();
          }
        });
      }

      /* barras dinámicas: ahora puede haber N equipos */
      const barras = Array.from(
        document.querySelectorAll(".barra")
      );
      const carriles = Array.from(
        document.querySelectorAll(".carril-race")
      );

      const TOTAL_FRAMES = 260;
      const START = 8, END = 92;
      let frame = 0, terminoCarrera = false, redirigiendo = false;
      let ultimoListos = 0, ultimoTotal = 0;

      function tJuego(clave, fallback = "") {
        const idioma = window.i18nJuego?.obtenerIdioma?.() || "es";
        return window.i18nJuego?.traducciones?.[idioma]?.[clave] || fallback;
      }
      function textoGruposListos(listos, total) {
        return `${listos}/${total} ${tJuego("ranking_grupos_listos", "grupos listos")}`;
      }
      function setTextoBotonContinuar() {
        if (!btnRankingListo || btnRankingListo.disabled) return;
        btnRankingListo.textContent = tJuego("ranking_continuar", "Continuar");
      }
      function setTextoBotonEsperando() {
        if (!btnRankingListo) return;
        btnRankingListo.textContent = tJuego("ranking_esperando", "Esperando...");
      }
      function aplicarTraduccionRankingDinamica() {
        if (rankingEstado) rankingEstado.textContent = textoGruposListos(ultimoListos, ultimoTotal);
        if (btnRankingListo) {
          if (btnRankingListo.disabled) setTextoBotonEsperando();
          else setTextoBotonContinuar();
        }
      }
      function aplicarBarrasParciales() {
        if (esRankingFinal) return;
        const fills = Array.from(document.querySelectorAll(".ranking-barra-fill"));
        if (!fills.length) return;
        const valores = fills.map(el => Number(el.dataset.tokens || 0));
        const max = Math.max(...valores, 1);
        fills.forEach(el => {
          const valor = Number(el.dataset.tokens || 0);
          const porcentaje = Math.max(8, Math.round((valor / max) * 100));
          el.style.width = `${porcentaje}%`;
        });
      }
      function easeInOutCubic(t) {
        return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
      }
      function actualizarEstadoRanking(data) {
        if (!rankingEstado) return;
        const listos = Number(
          esRankingFinal
            ? (data.gruposListosF6 || 0)
            : (data.gruposListosRanking || data.gruposListosF6 || 0)
        );
        const total = Number(data.totalGrupos || 0);
        ultimoListos = listos;
        ultimoTotal  = total;
        rankingEstado.textContent = textoGruposListos(listos, total);
        const miGrupo = (data.grupos || []).find(g => String(g.id) === String(grupoId));
        const miGrupoListo = esRankingFinal
          ? miGrupo?.listoF6
          : (miGrupo?.listoRanking || miGrupo?.listoF6);
        if (miGrupoListo && btnRankingListo) {
          btnRankingListo.disabled = true;
          setTextoBotonEsperando();
        }
      }
      async function refrescarEstadoRanking() {
        if (redirigiendo || !sesionId) return;
        try {
          const res = await fetch(`/sesion/${sesionId}/estado/`, {
            cache: "no-store", credentials: "same-origin"
          });
          if (!res.ok) return;
          const data = await res.json();
          actualizarEstadoRanking(data);
          if (data.faseActual && data.faseActual !== faseActualEsperada && data.rutaAlumno) {
            redirigiendo = true;
            window.location.href = data.rutaAlumno;
          }
        } catch (e) { console.error("Error consultando ranking:", e); }
      }

      if (btnRankingListo) {
        btnRankingListo.addEventListener("click", async () => {
          btnRankingListo.disabled = true;
          setTextoBotonEsperando();
          try {
            const res = await fetch(`/grupo/${grupoId}/listo/`, {
              method: "POST",
              credentials: "same-origin",
              headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken
              },
              body: JSON.stringify({ fase: faseClaveRanking })
            });
            const data = await res.json();
            if (!res.ok || !data.ok) throw new Error(data.error || "No se pudo marcar listo en ranking.");
            ultimoListos = Number(data.listos || 0);
            ultimoTotal  = Number(data.total  || 0);
            if (rankingEstado) rankingEstado.textContent = textoGruposListos(ultimoListos, ultimoTotal);
          } catch (e) {
            console.error("Error marcando listo ranking:", e);
            btnRankingListo.disabled = false;
            setTextoBotonContinuar();
          }
        });
      }

      window.addEventListener("idiomaJuegoCambiado", () => aplicarTraduccionRankingDinamica());
      setTextoBotonContinuar();

      if (!esRankingFinal) {
        aplicarBarrasParciales();
        refrescarEstadoRanking();
        setInterval(refrescarEstadoRanking, 1500);
        return;
      }

      /* ── animación de carrera ── */
      function animarCarrera() {
        if (terminoCarrera) return;
        frame++;
        const t   = Math.min(frame / TOTAL_FRAMES, 1);
        const pos = START + (END - START) * easeInOutCubic(t);
        barras.forEach(b => { if (b) b.style.width = `${pos}%`; });
        carriles.forEach(c => { if (pos > 20) c.classList.add("lit"); });

        if (frame >= TOTAL_FRAMES) {
          terminoCarrera = true;
          /* destello en el frente de cada barra */
          barras.forEach(b => b && b.classList.add("glow"));
          /* extra: fuegos al finalizar carrera */
          if (window.fwStart) window.fwStart(false, 5);

          setTimeout(() => {
            if (carrera) carrera.classList.add("fade-out");
            if (overlay) overlay.classList.add("visible");
          }, 300);
          setTimeout(() => {
            if (carrera) carrera.classList.add("hidden");
            if (overlay) overlay.classList.remove("visible");
            /* reproducir video cinemático antes del podio */
            window.mostrarPodioFinal = function () {
              const vo = document.getElementById("videoOverlay");
              if (vo) {
                vo.classList.remove("visible");
                vo.classList.add("fade-out");
              }
              setTimeout(() => {
                if (vo) { vo.style.display = "none"; vo.classList.remove("fade-out"); }
                if (podio) podio.classList.add("visible");
                if (window.fwStart) window.fwStart(true, 6);
                try {
                  if (audio) {
                    audio.currentTime = 0;
                    audio.volume = 1;
                    audio.play().catch(() => {});
                    /* reanudar música de fondo cuando termine el sonido de victoria */
                    audio.onended = function () {
                      const bg = document.getElementById("musica-ranking");
                      if (bg && !bg.muted) bg.play().catch(() => {});
                    };
                  }
                } catch (e) {}
              }, 700);
            };
            window.saltarVideo = function () {
              const vid = document.getElementById("videoMisionCumplida");
              if (vid) vid.pause();
              window.mostrarPodioFinal();
            };
            const vo = document.getElementById("videoOverlay");
            const vid = document.getElementById("videoMisionCumplida");
            if (vo && vid) {
              /* display:block antes de añadir .visible para que la transición funcione */
              vo.style.display = "block";
              requestAnimationFrame(() => {
                vo.classList.add("visible");
              });
              vid.currentTime = 0;
              /* pausar música de fondo para que no compita con el video */
              const musicaBg = document.getElementById("musica-ranking");
              if (musicaBg) musicaBg.pause();
              vid.play().catch(() => {});
              vid.onended = () => window.mostrarPodioFinal();
            } else {
              /* sin video: ir directo al podio */
              if (podio) podio.classList.add("visible");
              if (window.fwStart) window.fwStart(true, 6);
              try {
                if (audio) {
                  audio.currentTime = 0;
                  audio.volume = 1;
                  audio.play().catch(() => {});
                  /* reanudar música de fondo cuando termine el sonido de victoria */
                  audio.onended = function () {
                    const bg = document.getElementById("musica-ranking");
                    if (bg && !bg.muted) bg.play().catch(() => {});
                  };
                }
              } catch (e) {}
            }
          }, 2600);
          return;
        }
        requestAnimationFrame(animarCarrera);
      }

      /* la carrera arranca tras el reveal del suspenso (~5 s) */
      setTimeout(() => requestAnimationFrame(animarCarrera), 5000);

      refrescarEstadoRanking();
      setInterval(refrescarEstadoRanking, 1500);
    });
