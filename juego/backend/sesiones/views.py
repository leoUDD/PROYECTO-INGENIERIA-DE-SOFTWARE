from juego.backend.sesiones.services import (
    crear_alumnos_en_sesion,
    crear_grupos_para_alumnos,
    leer_filas_archivo,
)

from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render

from juego.backend.sesiones.services import leer_filas_archivo
from juego.models import Alumno, Profesor, Sesion


def registraralumnos(request):
    profesor = Profesor.objects.first()

    if not profesor:
        messages.warning(
            request,
            "Primero debes registrar un profesor."
        )
        return redirect("registrarprofesor")

    sesion_activa = (
        Sesion.objects
        .filter(profesor=profesor)
        .order_by("-fecha_creacion")
        .first()
    )

    if not sesion_activa:
        messages.warning(
            request,
            "Primero crea una sesión antes de cargar alumnos."
        )
        return redirect("crear_sesion")

    alumnos = (
        Alumno.objects
        .filter(
            profesor_idprofesor=profesor,
            sesion=sesion_activa,
        )
        .order_by("idalumno")
    )

    if request.method == "POST" and request.FILES.get("archivo_excel"):
        archivo = request.FILES["archivo_excel"]

        try:
            nombre_archivo = archivo.name.lower()

            if not nombre_archivo.endswith((".xlsx", ".csv")):
                messages.error(
                    request,
                    "Formato no soportado. Usa .xlsx o .csv."
                )

                return render(
                    request,
                    "registraralumnos.html",
                    {
                        "alumnos": alumnos,
                        "sesion_activa": sesion_activa,
                    },
                )

            filas = leer_filas_archivo(archivo)

            with transaction.atomic():
                for fila in filas:
                    Alumno.objects.create(
                        profesor_idprofesor=profesor,
                        sesion=sesion_activa,
                        emailalumno=fila.get("Correo", ""),
                        rutalumno=fila.get("RUT", ""),
                        nombrealumno=fila.get("Nombre", ""),
                        apellidopaternoalumno=fila.get(
                            "Apellido Paterno",
                            "",
                        ),
                        apellidomaternoalumno=fila.get(
                            "Apellido Materno",
                            "",
                        ),
                        carreraalumno=fila.get("Carrera", ""),
                    )

            messages.success(
                request,
                (
                    "Alumnos cargados correctamente para la sesión "
                    f"'{sesion_activa.nombre}'."
                ),
            )

            alumnos = (
                Alumno.objects
                .filter(
                    profesor_idprofesor=profesor,
                    sesion=sesion_activa,
                )
                .order_by("idalumno")
            )

        except Exception as error:
            messages.error(
                request,
                f"Error al leer el archivo: {error}"
            )

    return render(
        request,
        "registraralumnos.html",
        {
            "alumnos": alumnos,
            "sesion_activa": sesion_activa,
        },
    )


def control_sesion(request, sesion_id):
    sesion = get_object_or_404(Sesion, pk=sesion_id)
    grupos = Grupo.objects.filter(sesion=sesion).order_by("idgrupo")

    return render(request, "control_sesion.html", {
        "sesion": sesion,
        "grupos": grupos,
        "es_profesor_panel": True,
    })

@require_POST
def profesor_fase_anterior(request, sesion_id):
    sesion = get_object_or_404(Sesion, pk=sesion_id)

    fase_actual = sesion.fase_actual
    nueva_fase = fase_anterior_automatica(fase_actual)

    if nueva_fase == fase_actual:
        return JsonResponse({
            "ok": False,
            "error": f"La fase actual no está en el flujo: {fase_actual}"
        }, status=400)

    # Cambiar fase
    sesion.fase_actual = nueva_fase
    sesion.segundos_restantes = tiempo_por_fase(sesion, nueva_fase)
    sesion.timer_corriendo = False
    sesion.timer_inicio_at = None
    sesion.timer_fin_at = None
    sesion.inicio_fase_habilitado = False if nueva_fase in FASES_CON_INICIO_POR_ALUMNOS else True

    grupos = Grupo.objects.filter(sesion=sesion)

    # Limpieza para evitar que al retroceder vuelva a autoavanzar inmediatamente
    if nueva_fase == "intro_habilidades":
        grupos.update(
            listo_lobby=False,
            listo_f1=False,
            listo_f2=False,
            listo_f3=False,
            listo_f4=False,
            listo_f5=False,
            listo_f6=False,
            listo_ranking=False,
        )

    elif nueva_fase == "f1_bienvenida":
        grupos.update(listo_lobby=False)

    elif nueva_fase == "f1_conocidos":
        grupos.update(listo_lobby=False)

    elif nueva_fase == "f1_pre_sopa":
        grupos.update(listo_f1=False)

    elif nueva_fase == "f1_sopa":
        grupos.update(
            listo_f1=False,
            sopa_ganada=False,
            sopa_tiempo_segundos=None,
            sopa_completada_en=None,
        )

    elif nueva_fase == "f1_ranking":
        grupos.update(listo_f6=False, listo_ranking=False)

    elif nueva_fase == "mapa_f2_empatia":
        grupos.update(listo_f6=False, listo_ranking=False)

    elif nueva_fase == "f2_transicion":
        grupos.update(listo_f2=False)

    elif nueva_fase == "f2_tematicas":
        grupos.update(
            listo_f2=False,
            listo_f2_tematica=False,
            listo_f2_desafio=False,
        )

    elif nueva_fase == "f2_transicion_empatia":
        grupos.update(listo_f2_empatia=False)

    elif nueva_fase == "f2_bubblemap":
        grupos.update(
            listo_f2=False,
            bubble_tokens_otorgados=False,
        )

    elif nueva_fase == "f2_ranking":
        grupos.update(listo_f6=False, listo_ranking=False)

    elif nueva_fase == "mapa_f3_creatividad":
        grupos.update(listo_f6=False, listo_ranking=False)

    elif nueva_fase == "f3_transicion_creatividad":
        grupos.update(listo_f3=False)

    elif nueva_fase == "f3_lego":
        grupos.update(
            listo_inicio_f3=False,
            listo_f3=False,
            listo_f3_lego=False,
            lego_sin_foto=False,
        )

    elif nueva_fase == "f3_ranking":
        grupos.update(listo_f6=False, listo_ranking=False)

    elif nueva_fase == "mapa_f4_final":
        grupos.update(listo_f6=False, listo_ranking=False)

    elif nueva_fase == "f4_transicion_comunicacion":
        grupos.update(listo_f4=False)

    elif nueva_fase == "f4_construccion_pitch":
        grupos.update(listo_f4=False)

    elif nueva_fase == "f4_orden_pitch":
        grupos.update(
            listo_f4_orden=False,
            orden_presentacion=None,
        )
        sesion.orden_sorteado = False
        sesion.grupo_presentando = None

    elif nueva_fase == "f4_presentacion_pitch":
        grupos.update(listo_f5=False)

    elif nueva_fase == "f5_evaluacion_pitch":
        grupos.update(listo_f5=False)

    elif nueva_fase == "f6_ranking":
        grupos.update(listo_f6=False, listo_ranking=False)

    sesion.save()

    grupos_data = [
        {
            "id": g.idgrupo,
            "nombre": g.nombregrupo,
            "tokens": g.tokensgrupo or 0,
            "temaElegido": g.tema_elegido or "",
            "desafioNombre": g.desafio_nombre or "",
            "legoConFoto": bool(g.foto_lego),
            "legoSinFoto": g.lego_sin_foto,
            "pitchTexto": bool(g.pitch_texto),
            "listoLobby": g.listo_lobby,
            "listoF1": g.listo_f1,
            "listoF2": g.listo_f2_desafio,
            "listoF2Generico": g.listo_f2,
            "listoF2Empatia": g.listo_f2_empatia,
            "listoF3": g.listo_f3,
            "listoF3Lego": g.listo_f3_lego,
            "listoF4": g.listo_f4,
            "listoF4Orden": g.listo_f4_orden,
            "listoF5": g.listo_f5,
            "listoF6": g.listo_f6,
        }
        for g in Grupo.objects.filter(sesion=sesion).order_by("idgrupo")
    ]

    total_grupos = len(grupos_data)

    return JsonResponse({
        "ok": True,
        "esProfesor": True,
        "faseActual": sesion.fase_actual,
        "faseEtiqueta": ETIQUETA_FASE.get(sesion.fase_actual, sesion.fase_actual),
        "rutaAlumno": reverse(RUTA_POR_FASE.get(sesion.fase_actual, "pantalla_espera")),
        "timerCorriendo": sesion.timer_corriendo,
        "segundosRestantes": sesion.segundos_restantes or 0,
        "totalGrupos": total_grupos,
        "grupos": grupos_data,
        "listosInicio": 0,
        "totalListosInicio": total_grupos,
        "inicioFaseHabilitado": sesion.inicio_fase_habilitado,
    })

@require_POST
def profesor_actualizar_estado(request, sesion_id):
    sesion = get_object_or_404(Sesion, pk=sesion_id)
    payload = json.loads(request.body or "{}")

    fase_anterior = sesion.fase_actual
    nueva_fase = payload.get("faseActual")

    accion_timer = payload.get("accionTimer")

    if accion_timer == "reiniciar_fase":
        sesion.segundos_restantes = tiempo_por_fase(sesion, sesion.fase_actual)
        sesion.timer_corriendo = False
        sesion.timer_inicio_at = None
        sesion.timer_fin_at = None
        sesion.save()

    elif accion_timer == "iniciar":
        segundos = int(sesion.segundos_restantes or tiempo_por_fase(sesion, sesion.fase_actual))

        sesion.segundos_restantes = segundos
        sesion.timer_corriendo = segundos > 0
        sesion.timer_inicio_at = timezone.now() if segundos > 0 else None
        sesion.timer_fin_at = timezone.now() + timedelta(seconds=segundos) if segundos > 0 else None
        sesion.save()

    elif accion_timer == "detener":
        restantes = calcular_segundos_restantes(sesion)
        sesion.segundos_restantes = restantes
        sesion.timer_corriendo = False
        sesion.timer_inicio_at = None
        sesion.timer_fin_at = None
        sesion.save()

    if nueva_fase:
        if nueva_fase not in FASES_ORDEN:
            return JsonResponse({"ok": False, "error": "Pantalla inválida"}, status=400)
        sesion.fase_actual = nueva_fase

    if nueva_fase and nueva_fase != fase_anterior:
        sesion.segundos_restantes = tiempo_por_fase(sesion, nueva_fase)
        sesion.timer_corriendo = False
        sesion.timer_inicio_at = None
        sesion.timer_fin_at = None

        if nueva_fase == "f4_orden_pitch":
            Grupo.objects.filter(sesion=sesion).update(listo_f4_orden=False)
            sesion.orden_sorteado = False
            sesion.grupo_presentando = None
            Grupo.objects.filter(sesion=sesion).update(orden_presentacion=None)

        if nueva_fase == "f4_orden_pitch":
            Grupo.objects.filter(sesion=sesion).update(listo_f4_orden=False)

        if nueva_fase in FASES_CON_INICIO_POR_ALUMNOS:
            sesion.inicio_fase_habilitado = False
            sesion.save(update_fields=[
                "fase_actual",
                "segundos_restantes",
                "timer_corriendo",
                "timer_inicio_at",
                "timer_fin_at",
                "inicio_fase_habilitado",
            ])
            reset_listos_inicio_fase(sesion, nueva_fase)
        else:
            sesion.inicio_fase_habilitado = True

            if nueva_fase == "f5_evaluacion_pitch":
                Grupo.objects.filter(sesion=sesion).update(
                    listo_ranking=False,
                    recompensa_peer_otorgada=False,
                )

            if nueva_fase in {"f1_ranking", "f2_ranking", "f3_ranking", "f6_ranking"}:
                Grupo.objects.filter(sesion=sesion).update(
                    listo_f6=False,
                    listo_ranking=False,
                )

            sesion.save()

    if "timerCorriendo" in payload:
        timer_corriendo = bool(payload["timerCorriendo"])

        if timer_corriendo:
            segundos_base = int(payload.get("segundosRestantes", sesion.segundos_restantes or 0))
            sesion.segundos_restantes = max(segundos_base, 0)
            sesion.timer_corriendo = sesion.segundos_restantes > 0
            sesion.timer_inicio_at = timezone.now() if sesion.timer_corriendo else None
            sesion.timer_fin_at = (
                timezone.now() + timedelta(seconds=sesion.segundos_restantes)
                if sesion.timer_corriendo else None
            )
        else:
            restantes = calcular_segundos_restantes(sesion)
            sesion.segundos_restantes = restantes
            sesion.timer_corriendo = False
            sesion.timer_inicio_at = None
            sesion.timer_fin_at = None

    elif "segundosRestantes" in payload:
        sesion.segundos_restantes = max(int(payload["segundosRestantes"]), 0)
        sesion.timer_corriendo = False
        sesion.timer_inicio_at = None
        sesion.timer_fin_at = None

    sesion.save()

    return JsonResponse({
        "esProfesor": True,
        "ok": True,
        "faseActual": sesion.fase_actual,
        "faseEtiqueta": ETIQUETA_FASE.get(sesion.fase_actual, sesion.fase_actual),
        "rutaAlumno": reverse(RUTA_POR_FASE.get(sesion.fase_actual, "pantalla_espera")),
        "timerCorriendo": sesion.timer_corriendo,
        "segundosRestantes": calcular_segundos_restantes(sesion),
        **serializar_estado_pitch(sesion),
    })

@require_POST
def profesor_siguiente_fase(request, sesion_id):
    sesion = get_object_or_404(Sesion, pk=sesion_id)

    if sesion.fase_actual == "f2_tematicas":
        total = Grupo.objects.filter(sesion=sesion).count()
        listos = Grupo.objects.filter(sesion=sesion, listo_f2_desafio=True).count()

        if total == 0 or listos < total:
            return JsonResponse({
                "ok": False,
                "error": f"Aún faltan grupos por elegir desafío ({listos}/{total})."
            }, status=400)

    try:
        idx = FASES_ORDEN.index(sesion.fase_actual)
    except ValueError:
        return JsonResponse({"ok": False, "error": "Fase actual inválida"}, status=400)

    if idx + 1 >= len(FASES_ORDEN):
        return JsonResponse({"ok": False, "error": "Ya está en la última fase"}, status=400)

    nueva_fase = FASES_ORDEN[idx + 1]


    sesion.fase_actual = nueva_fase
    sesion.segundos_restantes = tiempo_por_fase(sesion, nueva_fase)
    sesion.timer_corriendo = False
    sesion.timer_inicio_at = None
    sesion.timer_fin_at = None


    if nueva_fase in {"f2_tematicas", "f5_evaluacion_pitch"}:
        ahora = timezone.now()
        sesion.timer_corriendo = sesion.segundos_restantes > 0
        sesion.timer_inicio_at = ahora if sesion.timer_corriendo else None
        sesion.timer_fin_at = ahora + timedelta(seconds=sesion.segundos_restantes) if sesion.timer_corriendo else None

    if nueva_fase == "f4_orden_pitch":
        Grupo.objects.filter(sesion=sesion).update(listo_f4_orden=False, orden_presentacion=None)
        sesion.orden_sorteado = False
        sesion.grupo_presentando = None

    if nueva_fase in FASES_CON_INICIO_POR_ALUMNOS:
        sesion.inicio_fase_habilitado = False
        sesion.save(update_fields=[
            "fase_actual",
            "segundos_restantes",
            "timer_corriendo",
            "timer_inicio_at",
            "timer_fin_at",
            "inicio_fase_habilitado",
        ])
        reset_listos_inicio_fase(sesion, nueva_fase)
    else:
        sesion.inicio_fase_habilitado = True
        sesion.save()

    return JsonResponse({
        "esProfesor": True,
        "ok": True,
        "faseActual": sesion.fase_actual,
        "faseEtiqueta": ETIQUETA_FASE.get(sesion.fase_actual, sesion.fase_actual),
        "rutaAlumno": reverse(RUTA_POR_FASE.get(sesion.fase_actual, "pantalla_espera")),
        "timerCorriendo": sesion.timer_corriendo,
        "segundosRestantes": calcular_segundos_restantes(sesion),
        **serializar_estado_pitch(sesion),
    })

@require_POST
def dev_timer_10_segundos(request, sesion_id):
    if not settings.DEBUG:
        return JsonResponse({
            "ok": False,
            "error": "Esta función solo está disponible en modo desarrollo."
        }, status=403)

    sesion = get_object_or_404(Sesion, pk=sesion_id)

    segundos = 10
    ahora = timezone.now()

    sesion.segundos_restantes = segundos
    sesion.timer_corriendo = True
    sesion.timer_inicio_at = ahora
    sesion.timer_fin_at = ahora + timedelta(seconds=segundos)
    sesion.save(update_fields=[
        "segundos_restantes",
        "timer_corriendo",
        "timer_inicio_at",
        "timer_fin_at",
    ])

    return JsonResponse({
        "ok": True,
        "segundosRestantes": segundos,
        "faseActual": sesion.fase_actual,
    })


@require_POST
def iniciar_timer_inicio_fase(request, sesion_id):
    sesion = get_object_or_404(Sesion, pk=sesion_id)

    if sesion.fase_actual not in FASES_CON_INICIO_POR_ALUMNOS:
        return JsonResponse({
            "ok": False,
            "error": "La fase actual no usa inicio grupal."
        }, status=400)

    if not sesion.inicio_fase_habilitado:
        return JsonResponse({
            "ok": False,
            "error": "La fase aún no está habilitada."
        }, status=400)

    if not sesion.timer_corriendo:
        iniciar_timer_de_sesion(sesion)
        sesion.refresh_from_db()

    return JsonResponse({
        "ok": True,
        "faseActual": sesion.fase_actual,
        "timerCorriendo": sesion.timer_corriendo,
        "segundosRestantes": int(sesion.segundos_restantes or 0),
    })

def crear_sesion(request):
    profesor = Profesor.objects.first()

    if not profesor:
        messages.warning(request, "Primero debes registrar un profesor.")
        return redirect("registrarprofesor")

    if request.method == "POST":
        nombre = (request.POST.get("nombre") or "").strip()
        email_profesor = (request.POST.get("email_profesor") or "").strip()
        facultad = (request.POST.get("facultad") or "").strip()

        modo_creacion = request.POST.get("modo_creacion", "recomendado")
        archivo = request.FILES.get("archivo_excel")

        cantidad_sesiones = int(request.POST.get("cantidad_sesiones") or 1)
        grupos_por_sesion = int(request.POST.get("grupos_por_sesion") or 1)

        if not nombre:
            messages.error(request, "Debes darle un nombre a la sesión.")
            return render(request, "crear_sesion.html")

        if not email_profesor:
            messages.error(request, "Debes ingresar el correo del profesor.")
            return render(request, "crear_sesion.html")

        if not facultad:
            messages.error(request, "Debes seleccionar una facultad.")
            return render(request, "crear_sesion.html")

        if not archivo:
            messages.error(request, "Debes subir el archivo de estudiantes.")
            return render(request, "crear_sesion.html")

        try:
            filas = leer_filas_archivo(archivo)

            if not filas:
                messages.error(request, "El archivo no tiene estudiantes.")
                return render(request, "crear_sesion.html")

            sesiones_creadas = []

            with transaction.atomic():

                profesor.emailprofesor = email_profesor
                profesor.facultad = facultad
                profesor.save()

                if modo_creacion == "dividir_dos":
                    cantidad_sesiones = 2
                    grupos_por_sesion = None

                elif modo_creacion == "personalizado":
                    cantidad_sesiones = max(1, cantidad_sesiones)
                    grupos_por_sesion = max(1, grupos_por_sesion)

                else:
                    cantidad_sesiones = 1
                    grupos_por_sesion = None

                total_alumnos = len(filas)
                inicio = 0

                for numero_sesion in range(1, cantidad_sesiones + 1):
                    alumnos_en_esta_sesion = total_alumnos // cantidad_sesiones

                    if numero_sesion <= total_alumnos % cantidad_sesiones:
                        alumnos_en_esta_sesion += 1

                    fin = inicio + alumnos_en_esta_sesion
                    filas_sesion = filas[inicio:fin]
                    inicio = fin

                    if cantidad_sesiones == 1:
                        nombre_sesion = nombre
                    else:
                        nombre_sesion = f"{nombre} - Sala {numero_sesion}"

                    sesion = Sesion.objects.create(
                        profesor=profesor,
                        nombre=nombre_sesion,
                        fase_actual="f1_bienvenida",
                        timer_corriendo=False,
                        segundos_restantes=0,
                    )

                    alumnos = crear_alumnos_en_sesion(filas_sesion, profesor, sesion)

                    crear_grupos_para_alumnos(
                        sesion,
                        alumnos,
                        cantidad_grupos_manual=grupos_por_sesion
                    )

                    sesiones_creadas.append({
                        "sesion": sesion,
                        "grupos": Grupo.objects.filter(sesion=sesion)
                        .prefetch_related("alumno_set")
                        .order_by("idgrupo"),
                    })

                messages.success(request, "Sesión creada correctamente.")

            return render(request, "crear_sesion.html", {
                "sesiones_creadas": sesiones_creadas,
            })

        except Exception as e:
            messages.error(request, f"No se pudo procesar la sesión: {e}")
            return render(request, "crear_sesion.html")

    return render(request, "crear_sesion.html")

def listar_sesiones(request):
    profesor = Profesor.objects.first()

    if not profesor:
        messages.warning(request, "Aún no hay profesores registrados.")
        return redirect("registrarprofesor")

    sesiones = Sesion.objects.filter(profesor=profesor).order_by("-fecha_creacion")

    sesiones_info = []

    for sesion in sesiones:
        sesiones_info.append({
            "sesion": sesion,
            "total_grupos": Grupo.objects.filter(sesion=sesion).count(),
            "total_alumnos": Alumno.objects.filter(sesion=sesion).count(),
        })

    return render(request, "listar_sesiones.html", {
        "sesiones_info": sesiones_info
    })

def registraralumnos(request):
    return cargar_alumnos(request)

@require_http_methods(["POST"])
def agregar_alumno_manual(request):
    """
    Agrega un alumno manualmente a la SESIÓN ACTIVA del profesor.
    """
    correo = (request.POST.get("email") or "").strip()
    nombre = (request.POST.get("nombre") or "").strip()
    ap_paterno = (request.POST.get("apellido_paterno") or "").strip()
    ap_materno = (request.POST.get("apellido_materno") or "").strip()
    carrera = (request.POST.get("carrera") or "").strip()

    if not correo or not nombre:
        messages.warning(request, "Correo y Nombre son obligatorios.")
        return redirect("registraralumnos")

    try:
        validate_email(correo)
    except ValidationError:
        messages.error(request, "El correo no es válido.")
        return redirect("registraralumnos")

    profesor = Profesor.objects.first()
    if not profesor:
        messages.warning(request, "Primero debes registrar un profesor.")
        return redirect("registrarprofesor")

    sesion_activa = (
        Sesion.objects.filter(profesor=profesor)
        .order_by('-fecha_creacion')
        .first()
    )
    if not sesion_activa:
        messages.warning(request, "Primero crea una sesión antes de agregar alumnos.")
        return redirect("crear_sesion")

    if Alumno.objects.filter(emailalumno=correo, profesor_idprofesor=profesor, sesion=sesion_activa).exists():
        messages.warning(request, "⚠️ Ya existe un alumno con ese correo en esta sesión.")
        return redirect("registraralumnos")

    try:
        with transaction.atomic():
            Alumno.objects.create(
                profesor_idprofesor=profesor,
                sesion=sesion_activa,
                emailalumno=correo,
                nombrealumno=nombre,
                apellidopaternoalumno=ap_paterno,
                apellidomaternoalumno=ap_materno,
                carreraalumno=carrera or "No especificada",
            )
        messages.success(
            request,
            f"✅ Alumno agregado correctamente a la sesión '{sesion_activa.nombre}'."
        )
    except Exception as e:
        messages.error(request, f"Ocurrió un error al agregar: {e}")

    return redirect("registraralumnos")

@require_http_methods(["POST"])
def eliminar_alumno(request, idalumno):
    alumno = get_object_or_404(Alumno, idalumno=idalumno)
    try:
        with transaction.atomic():
            alumno.delete()
        messages.success(request, f"Alumno '{alumno.nombrealumno}' eliminado correctamente.")
    except Exception as e:
        messages.error(request, f"Ocurrió un error al eliminar: {e}")
    return redirect("registraralumnos")

def preview_pantalla_profesor(request, sesion_id):
    sesion = get_object_or_404(Sesion, pk=sesion_id)

    plantilla_por_fase = {
        "lobby": "pantalla_espera_preview.html",

        "f1_bienvenida": "pantalla_inicio.html",
        "f1_conocidos": "conocidos.html",
        "f1_pre_sopa": "trabajoenequipo.html",
        "f1_sopa": "minijuego1.html",

        "f2_transicion": "transiciondesafio.html",
        "f2_tematicas": "tematicas.html",
        "f2_transicion_empatia": "transicionempatia.html",
        "f2_bubblemap": "bubblemap.html",

        "f3_transicion_creatividad": "transicioncreatividad.html",
        "f3_lego": "lego.html",

        "f4_transicion_comunicacion": "transicioncomunicacion.html",
        "f4_construccion_pitch": "pitch.html",
        "f4_orden_pitch": "orden_presentacion.html",
        "f4_presentacion_pitch": "presentar_pitch.html",

        "f5_transicion_apoyo": "transicionapoyo.html",
        "f5_evaluacion_pitch": "peer_review.html",

        "f6_ranking": "ranking.html",
        "reflexion": "reflexion.html",
    }

    template_name = plantilla_por_fase.get(sesion.fase_actual, "pantalla_espera_preview.html")

    grupo_dummy = Grupo.objects.filter(sesion=sesion).order_by("idgrupo").first()

    if not grupo_dummy:
        grupo_dummy = Grupo(
            sesion=sesion,
            nombregrupo="Grupo preview",
            tokensgrupo=10,
        )

    context = {
        "grupo": grupo_dummy,
        "preview_profesor": True,
    }

    return render(request, template_name, context)

def ver_como_grupo(request, grupo_id):
    grupo = get_object_or_404(Grupo, idgrupo=grupo_id)

    request.session["grupo_id"] = grupo.idgrupo
    request.session["sesion_id"] = grupo.sesion.idsesion

    request.session["modo_profesor"] = True 

    return redirect("pantalla_espera")