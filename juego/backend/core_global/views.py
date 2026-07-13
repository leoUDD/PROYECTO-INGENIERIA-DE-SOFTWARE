import json

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
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

from juego.backend.fase4.services import serializar_estado_pitch


# ============================================================
# IMPORT TEMPORAL F5 / PITCH
# ============================================================
# Estas funciones pertenecen a la lógica de evaluación de pitch.
# Cuando ordenemos F5, lo ideal es dejarlas en:
# juego/backend/fase5/services.py
#
# Por ahora queda protegido para que el servidor no se caiga si
# ese módulo todavía no existe.
try:
    from juego.backend.fase5.services import (
        evaluacion_actual_completa,
        avanzar_al_siguiente_pitch_o_ranking,
    )
except ImportError:
    evaluacion_actual_completa = None
    avanzar_al_siguiente_pitch_o_ranking = None


# ============================================================
# HELPERS INTERNOS
# ============================================================


def _contar_listos_por_campo(sesion, campo):
    total = Grupo.objects.filter(sesion=sesion).count()
    listos = Grupo.objects.filter(sesion=sesion, **{campo: True}).count()
    todos = total > 0 and listos == total

    return total, listos, todos


def _activar_inicio_fase_si_todos(sesion, todos):
    if todos and not sesion.inicio_fase_habilitado:
        sesion.inicio_fase_habilitado = True
        sesion.save(update_fields=["inicio_fase_habilitado"])


def _respuesta_listo(sesion, fase_actual, total, listos, todos, extra=None, status=200):
    data = {
        "ok": True,
        "fase": fase_actual,
        "faseActual": sesion.fase_actual,
        "total": total,
        "listos": listos,
        "gruposListos": listos,
        "totalGrupos": total,
        "todos_listos": todos,
    }

    if extra:
        data.update(extra)

    return JsonResponse(data, status=status)


def _resolver_nombre_url_alumno(request, fase_actual):
    nombre_url = RUTA_POR_FASE.get(fase_actual, "pantalla_espera")

    # Caso especial: conocidos puede ir a modo normal, rápido o prompt.
    if fase_actual == "f1_conocidos":
        modo = request.session.get("modo_conocidos")

        if modo == "rapido":
            nombre_url = "conocidos_rapido"
        elif modo == "normal":
            nombre_url = "conocidos"
        else:
            nombre_url = "promptconocidos"

    return nombre_url


def _serializar_grupo_estado(grupo):
    return {
        "esProfesor": True,
        "id": grupo.idgrupo,
        "nombre": grupo.nombregrupo,
        "tokens": grupo.tokensgrupo or 0,

        # Datos F2 / desafíos
        "temaElegido": grupo.tema_elegido or "",
        "desafioNombre": grupo.desafio_nombre or "",
        "desafioDescripcion": grupo.desafio_descripcion or "",
        "desafioIdExterno": grupo.desafio_id_externo or "",
        "bubbleTokensOtorgados": getattr(grupo, "bubble_tokens_otorgados", False),

        # Listos generales por fase
        "listoLobby": grupo.listo_lobby,
        "listoF1": grupo.listo_f1,
        "listoF2": grupo.listo_f2_desafio,
        "listoF2Tematicas": grupo.listo_f2_tematicas,
        "listoF2Generico": grupo.listo_f2,
        "listoF2Empatia": getattr(grupo, "listo_f2_empatia", False),
        "listoF3": grupo.listo_f3,
        "listoInicioF3": getattr(grupo, "listo_inicio_f3", False),
        "listoF3Lego": getattr(grupo, "listo_f3_lego", False),
        "listoF4": grupo.listo_f4,
        "listoF4Orden": getattr(grupo, "listo_f4_orden", False),
        "listoF5": getattr(grupo, "listo_f5", False),
        "listoF6": getattr(grupo, "listo_f6", False),

        # LEGO
        "legoSinFoto": getattr(grupo, "lego_sin_foto", False),
        "legoConFoto": (
            bool(getattr(grupo, "foto_lego", None))
            and getattr(grupo, "listo_f3_lego", False)
        ),
    }


def _contar_en_lista(grupos_data, clave):
    return sum(1 for grupo in grupos_data if grupo[clave])


def _todos_listos(total, listos):
    return total > 0 and listos == total


def _avanzar_sesion_a_fase(sesion, nueva_fase, inicio_fase_habilitado=None):
    if inicio_fase_habilitado is None:
        inicio_fase_habilitado = (
            False if nueva_fase in FASES_CON_INICIO_POR_ALUMNOS else True
        )

    sesion.fase_actual = nueva_fase
    sesion.segundos_restantes = tiempo_por_fase(sesion, nueva_fase)
    sesion.timer_corriendo = False
    sesion.timer_inicio_at = None
    sesion.timer_fin_at = None
    sesion.inicio_fase_habilitado = inicio_fase_habilitado

    sesion.save(update_fields=[
        "fase_actual",
        "segundos_restantes",
        "timer_corriendo",
        "timer_inicio_at",
        "timer_fin_at",
        "inicio_fase_habilitado",
    ])


# ============================================================
# PANTALLA DE ESPERA
# ============================================================

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


# ============================================================
# ESTADO GLOBAL DE SESIÓN
# ============================================================


@require_GET
def estado_sesion(request, sesion_id):
    sesion = get_object_or_404(Sesion, pk=sesion_id)


    if (
        sesion.fase_actual == "f5_evaluacion_pitch"
        and callable(evaluacion_actual_completa)
        and callable(avanzar_al_siguiente_pitch_o_ranking)
        and evaluacion_actual_completa(sesion)
    ):
        avanzar_al_siguiente_pitch_o_ranking(sesion)


    autoavanzar_si_todos_listos(sesion)
    sesion.refresh_from_db()

    fase_actual = sesion.fase_actual
    nombre_url = _resolver_nombre_url_alumno(request, fase_actual)

    grupos = Grupo.objects.filter(sesion=sesion).order_by("idgrupo")
    grupos_data = [_serializar_grupo_estado(grupo) for grupo in grupos]

    total_grupos = len(grupos_data)


    grupos_listos_lobby = _contar_en_lista(grupos_data, "listoLobby")
    todos_listos_lobby = _todos_listos(total_grupos, grupos_listos_lobby)

    grupos_listos_f1 = _contar_en_lista(grupos_data, "listoF1")
    todos_listos_f1 = _todos_listos(total_grupos, grupos_listos_f1)


    grupos_listos_f2_generico = _contar_en_lista(grupos_data, "listoF2Generico")
    todos_listos_f2_generico = _todos_listos(total_grupos, grupos_listos_f2_generico)

    grupos_listos_f2_tematicas = _contar_en_lista(grupos_data, "listoF2Tematicas")
    todos_listos_f2_tematicas = _todos_listos(total_grupos, grupos_listos_f2_tematicas)

    grupos_listos_f2 = _contar_en_lista(grupos_data, "listoF2")
    todos_listos_f2 = _todos_listos(total_grupos, grupos_listos_f2)

    grupos_listos_f2_empatia = _contar_en_lista(grupos_data, "listoF2Empatia")
    todos_listos_f2_empatia = _todos_listos(total_grupos, grupos_listos_f2_empatia)


    grupos_listos_f3 = _contar_en_lista(grupos_data, "listoF3")
    todos_listos_f3 = _todos_listos(total_grupos, grupos_listos_f3)

    grupos_listos_f3_lego = _contar_en_lista(grupos_data, "listoF3Lego")
    todos_listos_f3_lego = _todos_listos(total_grupos, grupos_listos_f3_lego)

    grupos_con_foto_lego = _contar_en_lista(grupos_data, "legoConFoto")
    grupos_sin_foto_lego = _contar_en_lista(grupos_data, "legoSinFoto")


    grupos_listos_f4 = _contar_en_lista(grupos_data, "listoF4")
    todos_listos_f4 = _todos_listos(total_grupos, grupos_listos_f4)

    grupos_listos_f4_orden = _contar_en_lista(grupos_data, "listoF4Orden")
    todos_listos_f4_orden = _todos_listos(total_grupos, grupos_listos_f4_orden)


    grupos_listos_f5 = _contar_en_lista(grupos_data, "listoF5")
    todos_listos_f5 = _todos_listos(total_grupos, grupos_listos_f5)

    grupos_listos_f6 = _contar_en_lista(grupos_data, "listoF6")
    todos_listos_f6 = _todos_listos(total_grupos, grupos_listos_f6)

    grupos_listos_ranking = Grupo.objects.filter(
        sesion=sesion,
        listo_ranking=True,
    ).count()

    todos_listos_ranking = (
        total_grupos > 0
        and grupos_listos_ranking == total_grupos
    )


    total_inicio, listos_inicio, todos_inicio = contar_listos_inicio_fase(
        sesion,
        sesion.fase_actual,
    )


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

    # ------------------------------------------------------------
    # Respuesta JSON global.
    # ------------------------------------------------------------
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

        # Lobby
        "gruposListosLobby": grupos_listos_lobby,
        "todosListosLobby": todos_listos_lobby,

        # F1
        "gruposListosF1": grupos_listos_f1,
        "todosListosF1": todos_listos_f1,

        # F2
        "gruposListosF2Tematicas": grupos_listos_f2_tematicas,
        "todosListosF2Tematicas": todos_listos_f2_tematicas,
        "gruposListosF2Generico": grupos_listos_f2_generico,
        "todosListosF2Generico": todos_listos_f2_generico,
        "gruposListosF2Empatia": grupos_listos_f2_empatia,
        "todosListosF2Empatia": todos_listos_f2_empatia,
        "gruposListosF2": grupos_listos_f2,
        "todosListosF2": todos_listos_f2,

        # F3
        "gruposListosF3Lego": grupos_listos_f3_lego,
        "todosListosF3Lego": todos_listos_f3_lego,
        "gruposConFotoLego": grupos_con_foto_lego,
        "gruposSinFotoLego": grupos_sin_foto_lego,
        "gruposListosF3": grupos_listos_f3,
        "todosListosF3": todos_listos_f3,

        # F4
        "gruposListosF4": grupos_listos_f4,
        "todosListosF4": todos_listos_f4,
        "gruposListosF4Orden": grupos_listos_f4_orden,
        "todosListosF4Orden": todos_listos_f4_orden,

        # F5
        "gruposListosF5": grupos_listos_f5,
        "todosListosF5": todos_listos_f5,

        # F6
        "gruposListosF6": grupos_listos_f6,
        "todosListosF6": todos_listos_f6,

        # Ranking
        "gruposListosRanking": grupos_listos_ranking,
        "todosListosRanking": todos_listos_ranking,

        # Inicio de fase
        "inicioFaseHabilitado": sesion.inicio_fase_habilitado,
        "totalListosInicio": total_inicio,
        "listosInicio": listos_inicio,
        "todosListosInicio": todos_inicio,
        "faseRequiereInicio": (
            sesion.fase_actual in FASES_CON_INICIO_POR_ALUMNOS
        ),

        # Pitch si corresponde
        **pitch_data,
    }

    return JsonResponse(data)


# ============================================================
# MARCAR GRUPO LISTO
# ============================================================


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

        total, listos, todos = _contar_listos_por_campo(sesion, "listo_lobby")

        if fase_actual == "f1_conocidos":
            _activar_inicio_fase_si_todos(sesion, todos)

        return _respuesta_listo(
            sesion,
            fase_actual,
            total,
            listos,
            todos,
            extra={
                "gruposListosLobby": listos,
                "todosListosLobby": todos,
                "inicio_fase_habilitado": (
                    sesion.inicio_fase_habilitado
                    if fase_actual == "f1_conocidos"
                    else True
                ),
                "segundosRestantes": sesion.segundos_restantes,
            },
        )

    # ============================================================
    # F1 — TRANSICIÓN TRABAJO EN EQUIPO
    # ============================================================
    if fase_actual == "f1_pre_sopa" and fase_clave == "f1":
        if not grupo.listo_f1:
            grupo.listo_f1 = True
            grupo.save(update_fields=["listo_f1"])

        total, listos, todos = _contar_listos_por_campo(sesion, "listo_f1")

        return _respuesta_listo(
            sesion,
            fase_actual,
            total,
            listos,
            todos,
            extra={
                "gruposListosF1": listos,
                "todosListosF1": todos,
            },
        )

    # ============================================================
    # F1 — INICIO SOPA DE LETRAS
    # ============================================================
    if fase_actual == "f1_sopa" and fase_clave in ["f1_sopa", "sopa", "f1", None, ""]:
        if not grupo.listo_f1:
            grupo.listo_f1 = True
            grupo.save(update_fields=["listo_f1"])

        total, listos, todos = _contar_listos_por_campo(sesion, "listo_f1")

        _activar_inicio_fase_si_todos(sesion, todos)

        return _respuesta_listo(
            sesion,
            fase_actual,
            total,
            listos,
            todos,
            extra={
                "gruposListosF1": listos,
                "todosListosF1": todos,
                "inicio_fase_habilitado": sesion.inicio_fase_habilitado,
                "segundosRestantes": sesion.segundos_restantes,
            },
        )

    # ============================================================
    # F2 — TRANSICIÓN DESAFÍOS
    # ============================================================
    if fase_actual == "f2_transicion" and fase_clave == "f2":
        if not grupo.listo_f2:
            grupo.listo_f2 = True
            grupo.save(update_fields=["listo_f2"])

        total, listos, todos = _contar_listos_por_campo(sesion, "listo_f2")

        return _respuesta_listo(
            sesion,
            fase_actual,
            total,
            listos,
            todos,
            extra={
                "gruposListosF2Generico": listos,
                "todosListosF2Generico": todos,
            },
        )

    # ============================================================
    # F2 — TEMÁTICAS
    # ============================================================
    if fase_actual == "f2_tematicas" and fase_clave == "f2_tematicas":
        if not grupo.listo_f2_tematicas:
            grupo.listo_f2_tematicas = True
            grupo.save(update_fields=["listo_f2_tematicas"])

        total, listos, todos = _contar_listos_por_campo(
            sesion,
            "listo_f2_tematicas",
        )

        _activar_inicio_fase_si_todos(sesion, todos)

        return _respuesta_listo(
            sesion,
            fase_actual,
            total,
            listos,
            todos,
            extra={
                "gruposListosF2Tematicas": listos,
                "todosListosF2Tematicas": todos,
                "inicio_fase_habilitado": sesion.inicio_fase_habilitado,
                "segundosRestantes": sesion.segundos_restantes,
            },
        )

    # ============================================================
    # F2 — TRANSICIÓN EMPATÍA
    # ============================================================
    if fase_actual == "f2_transicion_empatia" and fase_clave == "f2_empatia":
        if not getattr(grupo, "listo_f2_empatia", False):
            grupo.listo_f2_empatia = True
            grupo.save(update_fields=["listo_f2_empatia"])

        total, listos, todos = _contar_listos_por_campo(
            sesion,
            "listo_f2_empatia",
        )

        return _respuesta_listo(
            sesion,
            fase_actual,
            total,
            listos,
            todos,
            extra={
                "gruposListosF2Empatia": listos,
                "todosListosF2Empatia": todos,
            },
        )

    # ============================================================
    # F2 — BUBBLE MAP
    # ============================================================
    if fase_actual == "f2_bubblemap" and fase_clave == "f2_bubblemap":
        if not grupo.listo_f2:
            grupo.listo_f2 = True
            grupo.save(update_fields=["listo_f2"])

        total, listos, todos = _contar_listos_por_campo(sesion, "listo_f2")

        _activar_inicio_fase_si_todos(sesion, todos)

        return _respuesta_listo(
            sesion,
            fase_actual,
            total,
            listos,
            todos,
            extra={
                "gruposListosF2": listos,
                "todosListosF2": todos,
                "inicio_fase_habilitado": sesion.inicio_fase_habilitado,
                "segundosRestantes": sesion.segundos_restantes,
            },
        )

    # ============================================================
    # F3 — TRANSICIÓN CREATIVIDAD
    # ============================================================
    if fase_actual == "f3_transicion_creatividad" and fase_clave == "f3":
        if not grupo.listo_f3:
            grupo.listo_f3 = True
            grupo.save(update_fields=["listo_f3"])

        total, listos, todos = _contar_listos_por_campo(sesion, "listo_f3")

        return _respuesta_listo(
            sesion,
            fase_actual,
            total,
            listos,
            todos,
            extra={
                "gruposListosF3": listos,
                "todosListosF3": todos,
            },
        )

    # ============================================================
    # F3 — INICIO LEGO
    # ============================================================
    if fase_actual == "f3_lego" and fase_clave in ["inicio_f3", "f3_lego", "f3", None, ""]:
        if not grupo.listo_inicio_f3:
            grupo.listo_inicio_f3 = True
            grupo.save(update_fields=["listo_inicio_f3"])

        total, listos, todos = _contar_listos_por_campo(
            sesion,
            "listo_inicio_f3",
        )

        _activar_inicio_fase_si_todos(sesion, todos)

        return _respuesta_listo(
            sesion,
            fase_actual,
            total,
            listos,
            todos,
            extra={
                "gruposListosInicioF3": listos,
                "todosListosInicioF3": todos,
                "inicio_fase_habilitado": sesion.inicio_fase_habilitado,
                "segundosRestantes": sesion.segundos_restantes,
            },
        )

    # ============================================================
    # F4 — TRANSICIÓN COMUNICACIÓN
    # ============================================================
    if fase_actual == "f4_transicion_comunicacion" and fase_clave == "f4":
        if not grupo.listo_f4:
            grupo.listo_f4 = True
            grupo.save(update_fields=["listo_f4"])

        total, listos, todos = _contar_listos_por_campo(sesion, "listo_f4")

        return _respuesta_listo(
            sesion,
            fase_actual,
            total,
            listos,
            todos,
            extra={
                "gruposListosF4": listos,
                "todosListosF4": todos,
            },
        )

    # ============================================================
    # F4 — INICIO CONSTRUCCIÓN PITCH
    # ============================================================
    if fase_actual == "f4_construccion_pitch" and fase_clave in [
        "f4_pitch",
        "f4_construccion_pitch",
        "f4",
        None,
        "",
    ]:
        if not grupo.listo_f4:
            grupo.listo_f4 = True
            grupo.save(update_fields=["listo_f4"])

        total, listos, todos = _contar_listos_por_campo(sesion, "listo_f4")

        _activar_inicio_fase_si_todos(sesion, todos)

        return _respuesta_listo(
            sesion,
            fase_actual,
            total,
            listos,
            todos,
            extra={
                "gruposListosF4": listos,
                "todosListosF4": todos,
                "inicio_fase_habilitado": sesion.inicio_fase_habilitado,
                "segundosRestantes": sesion.segundos_restantes,
            },
        )

    # ============================================================
    # F4 — ORDEN PRESENTACIÓN PITCH
    # ============================================================
    if fase_actual == "f4_orden_pitch" and fase_clave in [
        "f4_orden_pitch",
        "orden_pitch",
        "f4_orden",
        None,
        "",
    ]:
        if not grupo.listo_f4_orden:
            grupo.listo_f4_orden = True
            grupo.save(update_fields=["listo_f4_orden"])

        total, listos, todos = _contar_listos_por_campo(
            sesion,
            "listo_f4_orden",
        )

        autoavanzar_si_todos_listos(sesion)
        sesion.refresh_from_db()

        return _respuesta_listo(
            sesion,
            fase_actual,
            total,
            listos,
            todos,
            extra={
                "rutaAlumno": reverse(
                    RUTA_POR_FASE.get(sesion.fase_actual, "pantalla_espera")
                ),
                "gruposListosF4Orden": listos,
                "todosListosF4Orden": todos,
                "ordenSorteado": getattr(sesion, "orden_sorteado", False),
            },
        )

    # ============================================================
    # RANKING PARCIAL
    # ============================================================
    if fase_actual in {"f1_ranking", "f2_ranking", "f3_ranking"} and fase_clave == "ranking":
        if not grupo.listo_ranking:
            grupo.listo_ranking = True
            grupo.save(update_fields=["listo_ranking"])

        total, listos, todos = _contar_listos_por_campo(
            sesion,
            "listo_ranking",
        )

        if todos:
            nueva_fase = siguiente_fase_automatica(fase_actual)

            _avanzar_sesion_a_fase(sesion, nueva_fase)

            Grupo.objects.filter(sesion=sesion).update(
                listo_ranking=False,
                listo_f6=False,
            )

            if nueva_fase in FASES_CON_INICIO_POR_ALUMNOS:
                reset_listos_inicio_fase(sesion, nueva_fase)

            return _respuesta_listo(
                sesion,
                fase_actual,
                total,
                listos,
                todos,
                extra={
                    "rutaAlumno": reverse(
                        RUTA_POR_FASE.get(sesion.fase_actual, "pantalla_espera")
                    ),
                    "gruposListosRanking": listos,
                    "todosListosRanking": todos,
                },
            )

        return _respuesta_listo(
            sesion,
            fase_actual,
            total,
            listos,
            todos,
            extra={
                "gruposListosRanking": listos,
                "todosListosRanking": todos,
            },
        )

    # ============================================================
    # RANKING FINAL
    # ============================================================
    if fase_actual == "f6_ranking" and fase_clave == "f6":
        if not grupo.listo_f6:
            grupo.listo_f6 = True
            grupo.save(update_fields=["listo_f6"])

        total, listos, todos = _contar_listos_por_campo(sesion, "listo_f6")

        if todos:
            nueva_fase = siguiente_fase_automatica(fase_actual)

            if nueva_fase == "reflexion":
                borrar_fotos_lego_sesion(sesion)

            _avanzar_sesion_a_fase(
                sesion,
                nueva_fase,
                inicio_fase_habilitado=True,
            )

            Grupo.objects.filter(sesion=sesion).update(
                listo_f6=False,
                listo_ranking=False,
            )

            return _respuesta_listo(
                sesion,
                fase_actual,
                total,
                listos,
                todos,
                extra={
                    "rutaAlumno": reverse(
                        RUTA_POR_FASE.get(sesion.fase_actual, "pantalla_espera")
                    ),
                    "gruposListosF6": listos,
                    "todosListosF6": todos,
                },
            )

        return _respuesta_listo(
            sesion,
            fase_actual,
            total,
            listos,
            todos,
            extra={
                "gruposListosF6": listos,
                "todosListosF6": todos,
            },
        )

    # ============================================================
    # SI NO COINCIDE NINGÚN CASO
    # ============================================================
    return JsonResponse({
        "ok": False,
        "error": (
            "No se pudo marcar listo. "
            f"Fase actual: {fase_actual}, fase recibida: {fase_clave}"
        ),
    }, status=400)

def introducciones(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")
    if not acceso_permitido(grupo, "introducciones"):
        return redirect("pantalla_espera")
    return render(request, "introducciones.html", {"grupo": grupo})

@never_cache
def continuar_desde_mapa(request):
    grupo = obtener_grupo_desde_session(request)

    if not grupo:
        return redirect("registro")

    sesion = grupo.sesion
    fase_actual = sesion.fase_actual

    mapa_a_fase = {
        "intro_habilidades": "f1_conocidos",
        "mapa_f2_empatia": "f2_transicion",
        "mapa_f3_creatividad": "f3_transicion_creatividad",
        "mapa_f4_final": "f4_transicion_comunicacion",
    }

    nueva_fase = mapa_a_fase.get(fase_actual)

    if not nueva_fase:
        return redirect(ruta_alumno_por_estado(grupo))

    sesion.fase_actual = nueva_fase
    sesion.segundos_restantes = tiempo_por_fase(sesion, nueva_fase)
    sesion.timer_corriendo = False
    sesion.timer_inicio_at = None
    sesion.timer_fin_at = None
    sesion.inicio_fase_habilitado = False if nueva_fase in FASES_CON_INICIO_POR_ALUMNOS else True
    sesion.save()

    if nueva_fase in FASES_CON_INICIO_POR_ALUMNOS:
        reset_listos_inicio_fase(sesion, nueva_fase)

    return redirect(ruta_alumno_por_estado(grupo))

@never_cache
def habilidades_intro(request):
    grupo = obtener_grupo_desde_session(request)

    if not grupo:
        return redirect("registro")

    sesion = grupo.sesion
    fase_actual = sesion.fase_actual

    estado_mapa = {
        "habilidad_activa": "trabajo en equipo",
        "habilidades_completadas": [],
        "ruta_continuar": reverse("continuar_desde_mapa"),
        "texto_boton": "CONTINUAR A TRABAJO EN EQUIPO",
        "titulo_mapa": "HABILIDADES DE MISIÓN",
    }

    if fase_actual in ["mapa_f2_empatia", "f2_transicion", "f2_tematicas", "f2_transicion_empatia", "f2_bubblemap", "f2_ranking"]:
        estado_mapa = {
            "habilidad_activa": "empatia",
            "habilidades_completadas": ["trabajo en equipo"],
            "ruta_continuar": reverse("continuar_desde_mapa"),
            "texto_boton": "CONTINUAR A EMPATÍA",
            "titulo_mapa": "HABILIDADES DE MISIÓN",
        }

    elif fase_actual in ["mapa_f3_creatividad", "f3_transicion_creatividad", "f3_lego", "f3_ranking"]:
        estado_mapa = {
            "habilidad_activa": "creatividad",
            "habilidades_completadas": ["trabajo en equipo", "empatia"],
            "ruta_continuar": reverse("continuar_desde_mapa"),
            "texto_boton": "CONTINUAR A CREATIVIDAD",
            "titulo_mapa": "HABILIDADES DE MISIÓN",
        }

    elif fase_actual in [
        "mapa_f4_final",
        "f4_transicion_comunicacion",
        "f4_construccion_pitch",
        "f4_orden_pitch",
        "f4_presentacion_pitch",
        "f5_evaluacion_pitch",
        "f6_ranking",
    ]:
        estado_mapa = {
            "habilidad_activa": "mision final",
            "habilidades_completadas": ["trabajo en equipo", "empatia", "creatividad"],
            "ruta_continuar": reverse("continuar_desde_mapa"),
            "texto_boton": "CONTINUAR A MISIÓN FINAL",
            "titulo_mapa": "MISIÓN FINAL",
        }

    return render(request, "habilidades_intro.html", {
    "grupo": grupo,
    "sesion": sesion,
    "estado_mapa": estado_mapa,
    "habilidades_completadas_json": json.dumps(
        estado_mapa["habilidades_completadas"],
        ensure_ascii=False
    ),
})