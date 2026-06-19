import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from juego.models import Grupo, Sesion

from juego.backend.core_global.constants import (
    RUTA_POR_FASE,
    ETIQUETA_FASE,
    FASES_CON_INICIO_POR_ALUMNOS,
)

from juego.backend.core_global.services import (
    obtener_grupo_desde_session,
    acceso_permitido,
    ruta_alumno_por_estado,
    calcular_segundos_restantes,
    autoavanzar_si_todos_listos,
    contar_listos_inicio_fase,
    siguiente_fase_automatica,
    tiempo_por_fase,
    reset_listos_inicio_fase,
    borrar_fotos_lego_sesion,
)


@never_cache
def pantalla_espera(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        messages.error(request, "Debes ingresar con tu código.")
        return redirect("registro")

    ruta = ruta_alumno_por_estado(grupo)
    if ruta != "pantalla_espera":
        return redirect(ruta)

    return render(request, "pantalla_espera.html", {"grupo": grupo})


@require_GET
def estado_sesion(request, sesion_id):
    sesion = get_object_or_404(Sesion, pk=sesion_id)

    if sesion.fase_actual == "f5_evaluacion_pitch" and evaluacion_actual_completa(sesion):
        avanzar_al_siguiente_pitch_o_ranking(sesion)

    autoavanzar_si_todos_listos(sesion)
    sesion.refresh_from_db()

    grupos = Grupo.objects.filter(sesion=sesion).order_by("idgrupo")

    fase_actual = sesion.fase_actual
    nombre_url = RUTA_POR_FASE.get(fase_actual, "pantalla_espera")
    if fase_actual == "f1_conocidos":
        modo = request.session.get("modo_conocidos")

        if modo == "rapido":
            nombre_url = "conocidos_rapido"
        elif modo == "normal":
            nombre_url = "conocidos"
        else:
            nombre_url = "promptconocidos"

    grupos_data = [
        {
            "esProfesor": True,
            "id": g.idgrupo,
            "nombre": g.nombregrupo,
           "tokens": g.tokensgrupo or 0,
           "temaElegido": g.tema_elegido or "",
            "desafioNombre": g.desafio_nombre or "",
            "desafioDescripcion": g.desafio_descripcion or "",
            "desafioIdExterno": g.desafio_id_externo or "",
            "bubbleTokensOtorgados": getattr(g, "bubble_tokens_otorgados", False),
            "listoLobby": g.listo_lobby,
            "listoF1": g.listo_f1,
            "listoF2": g.listo_f2_desafio,
            "listoF2Tematicas": g.listo_f2_tematicas,
           "listoF2Generico": g.listo_f2,
            "listoF2Empatia": getattr(g, "listo_f2_empatia", False),
            "listoF3": g.listo_f3,
            "listoInicioF3": getattr(g, "listo_inicio_f3", False),
           "listoF3Lego": getattr(g, "listo_f3_lego", False),
           "legoSinFoto": getattr(g, "lego_sin_foto", False),
           "legoConFoto": bool(getattr(g, "foto_lego", None)) and getattr(g, "listo_f3_lego", False),
           "listoF4": g.listo_f4,
           "listoF4Orden": getattr(g, "listo_f4_orden", False),
           "listoF5": getattr(g, "listo_f5", False),
          "listoF6": getattr(g, "listo_f6", False),
        }
        for g in grupos
]

    total_grupos = len(grupos_data)

    grupos_listos_lobby = sum(1 for g in grupos_data if g["listoLobby"])
    todos_listos_lobby = total_grupos > 0 and grupos_listos_lobby == total_grupos

    grupos_listos_f1 = sum(1 for g in grupos_data if g["listoF1"])
    todos_listos_f1 = total_grupos > 0 and grupos_listos_f1 == total_grupos

    grupos_listos_f2_generico = sum(1 for g in grupos_data if g["listoF2Generico"])
    todos_listos_f2_generico = total_grupos > 0 and grupos_listos_f2_generico == total_grupos

    grupos_listos_f2_tematicas = sum(1 for g in grupos_data if g["listoF2Tematicas"])
    todos_listos_f2_tematicas = total_grupos > 0 and grupos_listos_f2_tematicas == total_grupos

    grupos_listos_f2 = sum(1 for g in grupos_data if g["listoF2"])
    todos_listos_f2 = total_grupos > 0 and grupos_listos_f2 == total_grupos

    grupos_listos_f2_empatia = sum(1 for g in grupos_data if g["listoF2Empatia"])
    todos_listos_f2_empatia = total_grupos > 0 and grupos_listos_f2_empatia == total_grupos

    grupos_listos_f3 = sum(1 for g in grupos_data if g["listoF3"])
    todos_listos_f3 = total_grupos > 0 and grupos_listos_f3 == total_grupos
    grupos_listos_f3_lego = sum(1 for g in grupos_data if g["listoF3Lego"])
    todos_listos_f3_lego = total_grupos > 0 and grupos_listos_f3_lego == total_grupos

    grupos_con_foto_lego = sum(1 for g in grupos_data if g["legoConFoto"])
    grupos_sin_foto_lego = sum(1 for g in grupos_data if g["legoSinFoto"])
    grupos_listos_f4 = sum(1 for g in grupos_data if g["listoF4"])
    todos_listos_f4 = total_grupos > 0 and grupos_listos_f4 == total_grupos
    grupos_listos_f4_orden = sum(1 for g in grupos_data if g["listoF4Orden"])
    todos_listos_f4_orden = total_grupos > 0 and grupos_listos_f4_orden == total_grupos

    grupos_listos_f5 = sum(1 for g in grupos_data if g["listoF5"])
    todos_listos_f5 = total_grupos > 0 and grupos_listos_f5 == total_grupos

    grupos_listos_f6 = sum(1 for g in grupos_data if g["listoF6"])
    todos_listos_f6 = total_grupos > 0 and grupos_listos_f6 == total_grupos

    grupos_listos_ranking = Grupo.objects.filter(sesion=sesion, listo_ranking=True).count()
    todos_listos_ranking = total_grupos > 0 and grupos_listos_ranking == total_grupos
    total_inicio, listos_inicio, todos_inicio = contar_listos_inicio_fase(sesion, sesion.fase_actual)


    pitch_data = {}
    if fase_actual in {
        "f4_orden_pitch",
        "f4_presentacion_pitch",
        "f5_evaluacion_pitch",
        "f1_ranking",
        "f2_ranking",
        "f3_ranking",
        "f6_ranking",
    }:
        pitch_data = serializar_estado_pitch(sesion)


    data = {
        "sesionId": sesion.idsesion,
        "faseActual": fase_actual,
        "faseEtiqueta": ETIQUETA_FASE.get(fase_actual, fase_actual),
        "rutaAlumno": reverse(nombre_url),
        "timerCorriendo": sesion.timer_corriendo,
        "segundosRestantes": calcular_segundos_restantes(sesion),

        "totalGrupos": total_grupos,
        "grupos": grupos_data,
        "esProfesor": request.user.is_staff,

        "gruposListosLobby": grupos_listos_lobby,
        "todosListosLobby": todos_listos_lobby,

        "gruposListosF1": grupos_listos_f1,
        "todosListosF1": todos_listos_f1,

        "gruposListosF2Tematicas": grupos_listos_f2_tematicas,
        "todosListosF2Tematicas": todos_listos_f2_tematicas,
        "gruposListosF2Generico": grupos_listos_f2_generico,
        "todosListosF2Generico": todos_listos_f2_generico,
        "gruposListosF2Empatia": grupos_listos_f2_empatia,
        "todosListosF2Empatia": todos_listos_f2_empatia,
        "gruposListosF2": grupos_listos_f2,
        "todosListosF2": todos_listos_f2,

        "gruposListosF3Lego": grupos_listos_f3_lego,
        "todosListosF3Lego": todos_listos_f3_lego,
        "gruposConFotoLego": grupos_con_foto_lego,
        "gruposSinFotoLego": grupos_sin_foto_lego,
        "gruposListosF3": grupos_listos_f3,
        "todosListosF3": todos_listos_f3,

        "gruposListosF4": grupos_listos_f4,
        "todosListosF4": todos_listos_f4,
        "gruposListosF4Orden": grupos_listos_f4_orden,
        "todosListosF4Orden": todos_listos_f4_orden,

        "gruposListosF5": grupos_listos_f5,
        "todosListosF5": todos_listos_f5,

        "gruposListosF6": grupos_listos_f6,
        "todosListosF6": todos_listos_f6,

        "gruposListosRanking": grupos_listos_ranking,
        "todosListosRanking": todos_listos_ranking,

        "inicioFaseHabilitado": sesion.inicio_fase_habilitado,
        "totalListosInicio": total_inicio,
        "listosInicio": listos_inicio,
        "todosListosInicio": todos_inicio,
        "faseRequiereInicio": sesion.fase_actual in FASES_CON_INICIO_POR_ALUMNOS,

        **pitch_data,
    }

    return JsonResponse(data)

@require_POST
def marcar_grupo_listo(request, grupo_id):
    grupo = get_object_or_404(Grupo, pk=grupo_id)
    sesion = grupo.sesion
    fase_actual = sesion.fase_actual

    try:
        payload = json.loads(request.body or "{}")
    except Exception:
        payload = {}

    fase_clave = payload.get("fase")

    # ============================================================
    # LOBBY / BIENVENIDA / CONOCIDOS
    # ============================================================
    if fase_actual in ["lobby", "f1_bienvenida", "f1_conocidos"]:
        if not grupo.listo_lobby:
            grupo.listo_lobby = True
            grupo.save(update_fields=["listo_lobby"])

        total = Grupo.objects.filter(sesion=sesion).count()
        listos = Grupo.objects.filter(sesion=sesion, listo_lobby=True).count()
        todos = total > 0 and listos == total

        if fase_actual == "f1_conocidos" and todos and not sesion.inicio_fase_habilitado:
            sesion.inicio_fase_habilitado = True
            sesion.save(update_fields=["inicio_fase_habilitado"])

        return JsonResponse({
            "ok": True,
            "fase": fase_actual,
            "faseActual": sesion.fase_actual,
            "total": total,
            "listos": listos,
            "gruposListos": listos,
            "totalGrupos": total,
            "todos_listos": todos,
            "gruposListosLobby": listos,
            "todosListosLobby": todos,
            "inicio_fase_habilitado": sesion.inicio_fase_habilitado if fase_actual == "f1_conocidos" else True,
            "segundosRestantes": sesion.segundos_restantes,
        })

    # ============================================================
    # F1 — TRANSICIÓN TRABAJO EN EQUIPO
    # ============================================================
    if fase_actual == "f1_pre_sopa" and fase_clave == "f1":
        if not grupo.listo_f1:
            grupo.listo_f1 = True
            grupo.save(update_fields=["listo_f1"])

        total = Grupo.objects.filter(sesion=sesion).count()
        listos = Grupo.objects.filter(sesion=sesion, listo_f1=True).count()
        todos = total > 0 and listos == total

        return JsonResponse({
            "ok": True,
            "fase": fase_actual,
            "faseActual": sesion.fase_actual,
            "total": total,
            "listos": listos,
            "gruposListos": listos,
            "totalGrupos": total,
            "todos_listos": todos,
            "gruposListosF1": listos,
            "todosListosF1": todos,
        })

    # ============================================================
    # F1 — INICIO SOPA DE LETRAS
    # Botón "Listo para comenzar" dentro de la sopa.
    # ============================================================
    if fase_actual == "f1_sopa" and fase_clave in ["f1_sopa", "sopa", "f1", None, ""]:
        if not grupo.listo_f1:
            grupo.listo_f1 = True
            grupo.save(update_fields=["listo_f1"])

        total = Grupo.objects.filter(sesion=sesion).count()
        listos = Grupo.objects.filter(sesion=sesion, listo_f1=True).count()
        todos = total > 0 and listos == total

        if todos and not sesion.inicio_fase_habilitado:
            sesion.inicio_fase_habilitado = True
            sesion.save(update_fields=["inicio_fase_habilitado"])

        return JsonResponse({
            "ok": True,
            "fase": fase_actual,
            "faseActual": sesion.fase_actual,
            "total": total,
            "listos": listos,
            "gruposListos": listos,
            "totalGrupos": total,
            "todos_listos": todos,
            "gruposListosF1": listos,
            "todosListosF1": todos,
            "inicio_fase_habilitado": sesion.inicio_fase_habilitado,
            "segundosRestantes": sesion.segundos_restantes,
        })

    # ============================================================
    # F2 — TRANSICIÓN DESAFÍOS
    # ============================================================
    if fase_actual == "f2_transicion" and fase_clave == "f2":
        if not grupo.listo_f2:
            grupo.listo_f2 = True
            grupo.save(update_fields=["listo_f2"])

        total = Grupo.objects.filter(sesion=sesion).count()
        listos = Grupo.objects.filter(sesion=sesion, listo_f2=True).count()
        todos = total > 0 and listos == total

        return JsonResponse({
            "ok": True,
            "fase": fase_actual,
            "faseActual": sesion.fase_actual,
            "total": total,
            "listos": listos,
            "gruposListos": listos,
            "totalGrupos": total,
            "todos_listos": todos,
            "gruposListosF2Generico": listos,
            "todosListosF2Generico": todos,
        })

    # ============================================================
    # F2 — TEMÁTICAS
    # ============================================================
    if fase_actual == "f2_tematicas" and fase_clave == "f2_tematicas":
        if not grupo.listo_f2_tematicas:
            grupo.listo_f2_tematicas = True
            grupo.save(update_fields=["listo_f2_tematicas"])

        total = Grupo.objects.filter(sesion=sesion).count()
        listos = Grupo.objects.filter(sesion=sesion, listo_f2_tematicas=True).count()
        todos = total > 0 and listos == total

        if todos and not sesion.inicio_fase_habilitado:
            sesion.inicio_fase_habilitado = True
            sesion.save(update_fields=["inicio_fase_habilitado"])

        return JsonResponse({
            "ok": True,
            "fase": fase_actual,
            "faseActual": sesion.fase_actual,
            "total": total,
            "listos": listos,
            "gruposListos": listos,
            "totalGrupos": total,
            "todos_listos": todos,
            "gruposListosF2Tematicas": listos,
            "todosListosF2Tematicas": todos,
            "inicio_fase_habilitado": sesion.inicio_fase_habilitado,
            "segundosRestantes": sesion.segundos_restantes,
        })

    # ============================================================
    # F2 — TRANSICIÓN EMPATÍA
    # ============================================================
    if fase_actual == "f2_transicion_empatia" and fase_clave == "f2_empatia":
        if not getattr(grupo, "listo_f2_empatia", False):
            grupo.listo_f2_empatia = True
            grupo.save(update_fields=["listo_f2_empatia"])

        total = Grupo.objects.filter(sesion=sesion).count()
        listos = Grupo.objects.filter(sesion=sesion, listo_f2_empatia=True).count()
        todos = total > 0 and listos == total

        return JsonResponse({
            "ok": True,
            "fase": fase_actual,
            "faseActual": sesion.fase_actual,
            "total": total,
            "listos": listos,
            "gruposListos": listos,
            "totalGrupos": total,
            "todos_listos": todos,
            "gruposListosF2Empatia": listos,
            "todosListosF2Empatia": todos,
        })

    # ============================================================
    # F2 — BUBBLE MAP
    # ============================================================
    if fase_actual == "f2_bubblemap" and fase_clave == "f2_bubblemap":
        if not grupo.listo_f2:
            grupo.listo_f2 = True
            grupo.save(update_fields=["listo_f2"])

        total = Grupo.objects.filter(sesion=sesion).count()
        listos = Grupo.objects.filter(sesion=sesion, listo_f2=True).count()
        todos = total > 0 and listos == total

        if todos and not sesion.inicio_fase_habilitado:
            sesion.inicio_fase_habilitado = True
            sesion.save(update_fields=["inicio_fase_habilitado"])

        return JsonResponse({
            "ok": True,
            "fase": fase_actual,
            "faseActual": sesion.fase_actual,
            "total": total,
            "listos": listos,
            "gruposListos": listos,
            "totalGrupos": total,
            "todos_listos": todos,
            "gruposListosF2": listos,
            "todosListosF2": todos,
            "inicio_fase_habilitado": sesion.inicio_fase_habilitado,
            "segundosRestantes": sesion.segundos_restantes,
        })

    # ============================================================
    # F3 — TRANSICIÓN CREATIVIDAD
    # ============================================================
    if fase_actual == "f3_transicion_creatividad" and fase_clave == "f3":
        if not grupo.listo_f3:
            grupo.listo_f3 = True
            grupo.save(update_fields=["listo_f3"])

        total = Grupo.objects.filter(sesion=sesion).count()
        listos = Grupo.objects.filter(sesion=sesion, listo_f3=True).count()
        todos = total > 0 and listos == total

        return JsonResponse({
            "ok": True,
            "fase": fase_actual,
            "faseActual": sesion.fase_actual,
            "total": total,
            "listos": listos,
            "gruposListos": listos,
            "totalGrupos": total,
            "todos_listos": todos,
            "gruposListosF3": listos,
            "todosListosF3": todos,
        })

    # ============================================================
    # F3 — INICIO LEGO
    # ============================================================
    if fase_actual == "f3_lego" and fase_clave in ["inicio_f3", "f3_lego", "f3", None, ""]:
        if not grupo.listo_inicio_f3:
            grupo.listo_inicio_f3 = True
            grupo.save(update_fields=["listo_inicio_f3"])

        total = Grupo.objects.filter(sesion=sesion).count()
        listos = Grupo.objects.filter(sesion=sesion, listo_inicio_f3=True).count()
        todos = total > 0 and listos == total

        if todos and not sesion.inicio_fase_habilitado:
            sesion.inicio_fase_habilitado = True
            sesion.save(update_fields=["inicio_fase_habilitado"])

        return JsonResponse({
            "ok": True,
            "fase": fase_actual,
            "faseActual": sesion.fase_actual,
            "total": total,
            "listos": listos,
            "gruposListos": listos,
            "totalGrupos": total,
            "todos_listos": todos,
            "gruposListosInicioF3": listos,
            "todosListosInicioF3": todos,
            "inicio_fase_habilitado": sesion.inicio_fase_habilitado,
            "segundosRestantes": sesion.segundos_restantes,
        })

    # ============================================================
    # F4 — TRANSICIÓN COMUNICACIÓN
    # ============================================================
    if fase_actual == "f4_transicion_comunicacion" and fase_clave == "f4":
        if not grupo.listo_f4:
            grupo.listo_f4 = True
            grupo.save(update_fields=["listo_f4"])

        total = Grupo.objects.filter(sesion=sesion).count()
        listos = Grupo.objects.filter(sesion=sesion, listo_f4=True).count()
        todos = total > 0 and listos == total

        return JsonResponse({
            "ok": True,
            "fase": fase_actual,
            "faseActual": sesion.fase_actual,
            "total": total,
            "listos": listos,
            "gruposListos": listos,
            "totalGrupos": total,
            "todos_listos": todos,
            "gruposListosF4": listos,
            "todosListosF4": todos,
        })

    # ============================================================
    # F4 — INICIO CONSTRUCCIÓN PITCH
    # ============================================================
    if fase_actual == "f4_construccion_pitch" and fase_clave in ["f4_pitch", "f4_construccion_pitch", "f4", None, ""]:
        if not grupo.listo_f4:
            grupo.listo_f4 = True
            grupo.save(update_fields=["listo_f4"])

        total = Grupo.objects.filter(sesion=sesion).count()
        listos = Grupo.objects.filter(sesion=sesion, listo_f4=True).count()
        todos = total > 0 and listos == total

        if todos and not sesion.inicio_fase_habilitado:
            sesion.inicio_fase_habilitado = True
            sesion.save(update_fields=["inicio_fase_habilitado"])

        return JsonResponse({
            "ok": True,
            "fase": fase_actual,
            "faseActual": sesion.fase_actual,
            "total": total,
            "listos": listos,
            "gruposListos": listos,
            "totalGrupos": total,
            "todos_listos": todos,
            "gruposListosF4": listos,
            "todosListosF4": todos,
            "inicio_fase_habilitado": sesion.inicio_fase_habilitado,
            "segundosRestantes": sesion.segundos_restantes,
        })

    # ============================================================
    # F4 — ORDEN PRESENTACIÓN PITCH
    # ============================================================
    if fase_actual == "f4_orden_pitch" and fase_clave in ["f4_orden_pitch", "orden_pitch", "f4_orden", None, ""]:
        if not grupo.listo_f4_orden:
            grupo.listo_f4_orden = True
            grupo.save(update_fields=["listo_f4_orden"])

        total = Grupo.objects.filter(sesion=sesion).count()
        listos = Grupo.objects.filter(sesion=sesion, listo_f4_orden=True).count()
        todos = total > 0 and listos == total

        autoavanzar_si_todos_listos(sesion)
        sesion.refresh_from_db()

        return JsonResponse({
            "ok": True,
            "fase": fase_actual,
            "faseActual": sesion.fase_actual,
            "rutaAlumno": reverse(RUTA_POR_FASE.get(sesion.fase_actual, "pantalla_espera")),
            "total": total,
            "listos": listos,
            "gruposListos": listos,
            "totalGrupos": total,
            "todos_listos": todos,
            "gruposListosF4Orden": listos,
            "todosListosF4Orden": todos,
            "ordenSorteado": getattr(sesion, "orden_sorteado", False),
        })

    # ============================================================
    # RANKING PARCIAL
    # ============================================================
    if fase_actual in {"f1_ranking", "f2_ranking", "f3_ranking"} and fase_clave == "ranking":
        if not grupo.listo_ranking:
            grupo.listo_ranking = True
            grupo.save(update_fields=["listo_ranking"])

        total = Grupo.objects.filter(sesion=sesion).count()
        listos = Grupo.objects.filter(sesion=sesion, listo_ranking=True).count()
        todos = total > 0 and listos == total

        if todos:
            nueva_fase = siguiente_fase_automatica(fase_actual)

            sesion.fase_actual = nueva_fase
            sesion.segundos_restantes = tiempo_por_fase(sesion, nueva_fase)
            sesion.timer_corriendo = False
            sesion.timer_inicio_at = None
            sesion.timer_fin_at = None
            sesion.inicio_fase_habilitado = False if nueva_fase in FASES_CON_INICIO_POR_ALUMNOS else True
            sesion.save(update_fields=[
                "fase_actual",
                "segundos_restantes",
                "timer_corriendo",
                "timer_inicio_at",
                "timer_fin_at",
                "inicio_fase_habilitado",
            ])

            Grupo.objects.filter(sesion=sesion).update(
                listo_ranking=False,
                listo_f6=False,
            )

            if nueva_fase in FASES_CON_INICIO_POR_ALUMNOS:
                reset_listos_inicio_fase(sesion, nueva_fase)

            return JsonResponse({
                "ok": True,
                "fase": fase_actual,
                "faseActual": sesion.fase_actual,
                "rutaAlumno": reverse(RUTA_POR_FASE.get(sesion.fase_actual, "pantalla_espera")),
                "total": total,
                "listos": listos,
                "gruposListos": listos,
                "totalGrupos": total,
                "todos_listos": todos,
                "gruposListosRanking": listos,
                "todosListosRanking": todos,
            })

        return JsonResponse({
            "ok": True,
            "fase": fase_actual,
            "faseActual": sesion.fase_actual,
            "total": total,
            "listos": listos,
            "gruposListos": listos,
            "totalGrupos": total,
            "todos_listos": todos,
            "gruposListosRanking": listos,
            "todosListosRanking": todos,
        })

    # ============================================================
    # RANKING FINAL
    # ============================================================
    if fase_actual == "f6_ranking" and fase_clave == "f6":
        if not grupo.listo_f6:
            grupo.listo_f6 = True
            grupo.save(update_fields=["listo_f6"])

        total = Grupo.objects.filter(sesion=sesion).count()
        listos = Grupo.objects.filter(sesion=sesion, listo_f6=True).count()
        todos = total > 0 and listos == total

        if todos:
            nueva_fase = siguiente_fase_automatica(fase_actual)
            if nueva_fase == "reflexion":
                borrar_fotos_lego_sesion(sesion)
            sesion.fase_actual = nueva_fase
            sesion.segundos_restantes = tiempo_por_fase(sesion, nueva_fase)
            sesion.timer_corriendo = False
            sesion.timer_inicio_at = None
            sesion.timer_fin_at = None
            sesion.inicio_fase_habilitado = True
            sesion.save(update_fields=[
                "fase_actual",
                "segundos_restantes",
                "timer_corriendo",
                "timer_inicio_at",
                "timer_fin_at",
                "inicio_fase_habilitado",
            ])

            Grupo.objects.filter(sesion=sesion).update(
                listo_f6=False,
                listo_ranking=False,
            )

            return JsonResponse({
                "ok": True,
                "fase": fase_actual,
                "faseActual": sesion.fase_actual,
                "rutaAlumno": reverse(RUTA_POR_FASE.get(sesion.fase_actual, "pantalla_espera")),
                "total": total,
                "listos": listos,
                "gruposListos": listos,
                "totalGrupos": total,
                "todos_listos": todos,
                "gruposListosF6": listos,
                "todosListosF6": todos,
            })

        return JsonResponse({
            "ok": True,
            "fase": fase_actual,
            "faseActual": sesion.fase_actual,
            "total": total,
            "listos": listos,
            "gruposListos": listos,
            "totalGrupos": total,
            "todos_listos": todos,
            "gruposListosF6": listos,
            "todosListosF6": todos,
        })

    # ============================================================
    # SI NO COINCIDE NINGÚN CASO
    # ============================================================
    return JsonResponse({
        "ok": False,
        "error": f"No se pudo marcar listo. Fase actual: {fase_actual}, fase recibida: {fase_clave}"
    }, status=400)