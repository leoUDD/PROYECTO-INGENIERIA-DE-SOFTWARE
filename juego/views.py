#NUEVO
from django.shortcuts import render, redirect
from .forms import FotoLegoForm
from django.views.decorators.http import require_GET, require_POST
import json
from datetime import timedelta
from django.views.decorators.cache import never_cache
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.http import JsonResponse
#NUEVO CIERRRE
from django.shortcuts import redirect, render
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .tematicas_data import get_theme
import openpyxl
import pandas as pd
from .models import Alumno, Profesor, Usuario, Grupo, Desafio, Idadministrador, Sesion, Reto, Retogrupo, Evaluacion, PalabraSopaEncontrada
from django.db import transaction
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import secrets
from django.shortcuts import get_object_or_404
import string
import random
from math import ceil
from django.utils import timezone
from django.db.models import F



FASES_ORDEN = [
    "f1_bienvenida",
    "f1_conocidos",
    "f1_pre_sopa",
    "f1_sopa",

    "f2_transicion",
    "f2_tematicas",
    "f2_transicion_empatia",
    "f2_bubblemap",

    "f3_transicion_creatividad",
    "f3_lego",

    "f4_transicion_comunicacion",
    "f4_construccion_pitch",
    "f4_orden_pitch",
    "f4_presentacion_pitch",
    "f5_evaluacion_pitch",

    "f6_ranking",
    "reflexion",
]

RUTA_POR_FASE = {
    "lobby": "pantalla_espera",

    "f1_bienvenida": "pantalla_inicio",
    "f1_conocidos": "conocidos",
    "f1_pre_sopa": "trabajoenequipo",
    "f1_sopa": "minijuego1",

    "f2_transicion": "transiciondesafio",
    "f2_tematicas": "tematicas",
    "f2_transicion_empatia": "transicionempatia",
    "f2_bubblemap": "bubblemap",

    "f3_transicion_creatividad": "transicioncreatividad",
    "f3_lego": "lego",

    "f4_transicion_comunicacion": "transicioncomunicacion",
    "f4_construccion_pitch": "pitch",
    "f4_orden_pitch": "orden_presentacion_alumno",
    "f4_presentacion_pitch": "presentar_pitch",

    "f5_transicion_apoyo": "transicionapoyo",
    "f5_evaluacion_pitch": "peer_review",

    "f6_ranking": "ranking",
    "reflexion": "reflexion",
}

ETIQUETA_FASE = {

    "f1_bienvenida": "F1 · Bienvenida",
    "f1_conocidos": "F1 · Conocerse",
    "f1_pre_sopa": "F1 · Trabajo en equipo",
    "f1_sopa": "F1 · Sopa de letras",

    "f2_transicion": "F2 · Desafíos",
    "f2_tematicas": "F2 · Temáticas",
    "f2_transicion_empatia": "F2 · Transición Empatía",
    "f2_bubblemap": "F2 · Bubble Map",

    "f3_transicion_creatividad": "F3 · Transición Creatividad",
    "f3_lego": "F3 · Lego",

    "f4_transicion_comunicacion": "F4 · Transición Comunicación",
    "f4_construccion_pitch": "F4 · Construcción pitch",
    "f4_orden_pitch": "F4 · Sorteo orden pitch",
    "f4_presentacion_pitch": "F4 · Presentación pitch",

    "f5_transicion_apoyo": "F5 · Transición Apoyo",
    "f5_evaluacion_pitch": "F5 · Evaluación pitch",

    "f6_ranking": "Ranking",
    "reflexion": "Cierre",
}

FASES_CON_INICIO_POR_ALUMNOS = {
    "f1_conocidos",
    "f1_sopa",
    "f2_bubblemap",
    "f3_lego",
    "f4_construccion_pitch",
}


def reset_listos_inicio_fase(sesion, fase):
    grupos = Grupo.objects.filter(sesion=sesion)

    if fase == "f1_conocidos":
        grupos.update(listo_lobby=False)

    elif fase == "f1_sopa":
        grupos.update(listo_f1=False)

    elif fase == "f2_bubblemap":
        grupos.update(listo_f2=False)

    elif fase == "f3_lego":
        grupos.update(listo_inicio_f3=False)
        grupos.update(listo_f3=False)

    elif fase == "f4_construccion_pitch":
        grupos.update(listo_f4=False)

    sesion.inicio_fase_habilitado = False
    sesion.save(update_fields=["inicio_fase_habilitado"])


def contar_listos_inicio_fase(sesion, fase):
    grupos = Grupo.objects.filter(sesion=sesion)
    total = grupos.count()

    if fase == "f1_conocidos":
        listos = grupos.filter(listo_lobby=True).count()

    elif fase == "f1_sopa":
        listos = grupos.filter(listo_f1=True).count()

    elif fase == "f2_bubblemap":
        listos = grupos.filter(listo_f2=True).count()

    elif fase == "f3_lego":
        listos = grupos.filter(listo_inicio_f3=True).count()

    elif fase == "f4_construccion_pitch":
        listos = grupos.filter(listo_f4=True).count()

    else:
        listos = total

    return total, listos, (total > 0 and listos == total)


def iniciar_timer_de_sesion(sesion):
    segundos = int(sesion.segundos_restantes or 0)

    if segundos <= 0:
        return

    ahora = timezone.now()

    sesion.timer_corriendo = True
    sesion.timer_inicio_at = ahora
    sesion.timer_fin_at = ahora + timedelta(seconds=segundos)
    sesion.save(update_fields=[
        "timer_corriendo",
        "timer_inicio_at",
        "timer_fin_at",
    ])


def obtener_grupo_desde_session(request):
    grupo_id = request.session.get("grupo_id")
    sesion_id = request.session.get("sesion_id")

    print("obtener_grupo_desde_session -> grupo_id:", grupo_id, "| sesion_id:", sesion_id)

    if not grupo_id or not sesion_id:
        return None

    try:
        grupo = Grupo.objects.select_related("sesion").get(
            pk=grupo_id,
            sesion_id=sesion_id,
        )
    except Grupo.DoesNotExist:
        print("obtener_grupo_desde_session -> grupo no existe, flush session")
        request.session.flush()
        return None

    print("obtener_grupo_desde_session -> grupo real:", grupo.idgrupo, "| nombre:", grupo.nombregrupo)
    return grupo

def salir_grupo(request):
    request.session.flush()
    messages.success(request, "Sesión del grupo cerrada correctamente.")
    return redirect("registro")

def siguiente_fase_automatica(fase_actual):
    orden = [
        "lobby",
        "f1_bienvenida",
        "f1_conocidos",
        "f1_pre_sopa",
        "f1_sopa",
        "f2_transicion",
        "f2_tematicas",
        "f2_transicion_empatia",
        "f2_bubblemap",
        "f3_transicion_creatividad",
        "f3_lego",
        "f4_transicion_comunicacion",
        "f4_construccion_pitch",
        "f4_orden_pitch",
        "f4_presentacion_pitch",
        "f5_evaluacion_pitch",
        "f6_ranking",
        "reflexion",
    ]
    try:
        idx = orden.index(fase_actual)
        if idx + 1 < len(orden):
            return orden[idx + 1]
    except ValueError:
        pass
    return fase_actual

#CAMBIAR TIMERS
def tiempo_por_fase(sesion, fase):
    tiempos = {
        "f1_conocidos": 10,
        "f1_pre_sopa": 0,
        "f1_sopa": 60,

        "f2_transicion": 0,
        "f2_tematicas": 0,
        "f2_transicion_empatia": 0,
        "f2_bubblemap": 10,

        "f3_transicion_creatividad": 0,
        "f3_lego": 10,

        "f4_transicion_comunicacion": 0,
        "f4_construccion_pitch": 10,
        "f4_orden_pitch": 0,
        "f4_presentacion_pitch": 10,

        "f5_evaluacion_pitch": 0,
        "f6_ranking": 0,
        "reflexion": 0,
        "f1_bienvenida": 0,
        "lobby": 0,
    }
    return int(tiempos.get(fase, 0))


def calcular_segundos_restantes(sesion):
    if not sesion.timer_corriendo or not sesion.timer_fin_at:
        return max(int(sesion.segundos_restantes or 0), 0)

    restantes = int((sesion.timer_fin_at - timezone.now()).total_seconds())

    if restantes <= 0:
        fase_vencida = sesion.fase_actual

        sesion.timer_corriendo = False
        sesion.segundos_restantes = 0
        sesion.timer_inicio_at = None
        sesion.timer_fin_at = None

        if fase_vencida == "f4_presentacion_pitch":
            sesion.fase_actual = "f5_evaluacion_pitch"
            sesion.save(update_fields=[
                "fase_actual",
                "timer_corriendo",
                "segundos_restantes",
                "timer_inicio_at",
                "timer_fin_at",
            ])
            return 0

        fases_con_autoavance = {
            "f1_conocidos",
            "f1_sopa",
            "f2_bubblemap",
            "f4_construccion_pitch",
        }

        if fase_vencida in fases_con_autoavance:
            nueva_fase = siguiente_fase_automatica(fase_vencida)
            sesion.fase_actual = nueva_fase
            sesion.segundos_restantes = tiempo_por_fase(sesion, nueva_fase)

            if nueva_fase in FASES_CON_INICIO_POR_ALUMNOS:
                sesion.inicio_fase_habilitado = False
                sesion.save(update_fields=[
                    "fase_actual",
                    "timer_corriendo",
                    "segundos_restantes",
                    "timer_inicio_at",
                    "timer_fin_at",
                    "inicio_fase_habilitado",
                ])
                reset_listos_inicio_fase(sesion, nueva_fase)
                return 0

        sesion.save(update_fields=[
            "fase_actual",
            "timer_corriendo",
            "segundos_restantes",
            "timer_inicio_at",
            "timer_fin_at",
        ])
        return 0

    return max(restantes, 0)

def autoavanzar_si_todos_listos(sesion):
    grupos = Grupo.objects.filter(sesion=sesion)
    total = grupos.count()

    if total == 0:
        return False

    fase_actual = sesion.fase_actual
    nueva_fase = None

    if fase_actual == "f1_bienvenida":
        if grupos.filter(listo_lobby=True).count() == total:
            nueva_fase = "f1_conocidos"

    elif fase_actual == "f1_pre_sopa":
        if grupos.filter(listo_f1=True).count() == total:
            nueva_fase = "f1_sopa"

    elif fase_actual == "f2_transicion":
        if grupos.filter(listo_f2=True).count() == total:
            nueva_fase = "f2_tematicas"

    elif fase_actual == "f2_tematicas":
        if grupos.filter(listo_f2_desafio=True).count() == total:
            nueva_fase = "f2_transicion_empatia"

    elif fase_actual == "f2_transicion_empatia":
        if grupos.filter(listo_f2_empatia=True).count() == total:
            nueva_fase = "f2_bubblemap"

    elif fase_actual == "f3_transicion_creatividad":
        if grupos.filter(listo_f3=True).count() == total:
            nueva_fase = "f3_lego"

    elif fase_actual == "f3_lego":
        if grupos.filter(listo_f3_lego=True).count() == total:
            nueva_fase = "f4_transicion_comunicacion"

    elif fase_actual == "f4_transicion_comunicacion":
        if grupos.filter(listo_f4=True).count() == total:
            nueva_fase = "f4_construccion_pitch"

    elif fase_actual == "f6_ranking":
        if grupos.filter(listo_f6=True).count() == total:
            nueva_fase = "reflexion"

    if not nueva_fase:
        return False

    sesion.fase_actual = nueva_fase
    sesion.segundos_restantes = tiempo_por_fase(sesion, nueva_fase)
    sesion.timer_corriendo = False
    sesion.timer_inicio_at = None
    sesion.timer_fin_at = None

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
        return True

    sesion.inicio_fase_habilitado = True
    sesion.save(update_fields=[
        "fase_actual",
        "segundos_restantes",
        "timer_corriendo",
        "timer_inicio_at",
        "timer_fin_at",
        "inicio_fase_habilitado",
    ])
    return True


def peer_review_completado(grupo):
    sesion = grupo.sesion
    grupo_actual = sesion.grupo_presentando

    if not grupo_actual:
        return False

    if grupo.pk == grupo_actual.pk:
        return False

    return Evaluacion.objects.filter(
        sesion=sesion,
        grupo_evaluador=grupo,
        grupo_evaluado=grupo_actual,
    ).exists()


def ruta_alumno_por_estado(grupo):
    fase = grupo.sesion.fase_actual

    if fase == "f2_tematicas":
        if not (grupo.tema_elegido or "").strip():
            return "tematicas"
        return "desafios"

    if fase == "f5_evaluacion_pitch":
        return "peer_review"

    return RUTA_POR_FASE.get(fase, "pantalla_espera")

def acceso_permitido(grupo, nombre_vista):
    if not grupo or not grupo.sesion:
        return False

    fases_por_vista = {
        "pantalla_espera": ["lobby"],

        "pantalla_inicio": ["f1_bienvenida"],
        "conocidos": ["f1_conocidos"],
        "trabajoenequipo": ["f1_pre_sopa"],
        "minijuego1": ["f1_sopa"],

        "transiciondesafio": ["f2_transicion"],
        "tematicas": ["f2_tematicas"],
        "desafios": ["f2_tematicas"],
        "transicionempatia": ["f2_transicion_empatia"],
        "bubblemap": ["f2_bubblemap"],

        "transicioncreatividad": ["f3_transicion_creatividad"],
        "lego": ["f3_lego"],

        "transicioncomunicacion": ["f4_transicion_comunicacion"],
        "pitch": ["f4_construccion_pitch"],
        "orden_presentacion_alumno": ["f4_orden_pitch"],
        "presentar_pitch": ["f4_presentacion_pitch"],

        "transicionapoyo": ["f5_transicion_apoyo"],
        "peer_review": ["f5_evaluacion_pitch"],
        "mision_cumplida": ["f5_evaluacion_pitch"],

        "ranking": ["f6_ranking"],
        "reflexion": ["reflexion"],
    }

    return grupo.sesion.fase_actual in fases_por_vista.get(nombre_vista, [])

def espera_eleccion(request):
    grupo = obtener_grupo_desde_session(request)

    if not grupo:
        return redirect("registro")

    sesion = grupo.sesion
    grupos = Grupo.objects.filter(sesion=sesion)

    grupos_listos = grupos.filter(listo_f2_desafio=True).count()
    total_grupos = grupos.count()

    return render(request, "espera_eleccion.html", {
        "grupo": grupo,
        "tema": grupo.tema_elegido or "No seleccionada",
        "desafio_nombre": grupo.desafio_nombre or "No seleccionado",
        "grupos_listos": grupos_listos,
        "total_grupos": total_grupos,
    })

def serializar_estado_pitch(sesion, grupo_solicitante=None):
    grupo_actual = sesion.grupo_presentando

    orden_pitch = list(
        Grupo.objects.filter(sesion=sesion, orden_presentacion__isnull=False)
        .order_by("orden_presentacion")
        .values("idgrupo", "nombregrupo", "orden_presentacion")
    )

    foto_lego_url = None
    if grupo_actual and grupo_actual.foto_lego:
        try:
            foto_lego_url = grupo_actual.foto_lego.url
        except Exception:
            foto_lego_url = None

    segundos_restantes = max(int(sesion.segundos_restantes or 0), 0)
    if sesion.timer_corriendo and sesion.timer_fin_at:
        segundos_restantes = max(int((sesion.timer_fin_at - timezone.now()).total_seconds()), 0)

    return {
        "grupoActual": {
            "id": grupo_actual.idgrupo,
            "nombre": grupo_actual.nombregrupo,
            "fotoLego": foto_lego_url,
            "orden": grupo_actual.orden_presentacion,
        } if grupo_actual else None,
        "ordenPitch": [
            {
                "id": g["idgrupo"],
                "nombre": g["nombregrupo"],
                "orden": g["orden_presentacion"],
            }
            for g in orden_pitch
        ],
        "timerCorriendo": sesion.timer_corriendo,
        "segundosRestantes": segundos_restantes,
        "miPitch": grupo_solicitante.pitch_texto if grupo_solicitante else "",
        "miEquipoPresenta": (
    grupo_solicitante and grupo_actual and
    grupo_solicitante.idgrupo == grupo_actual.idgrupo
),
    }


#PRESENTACION PITCH/LEGO
@require_GET
@never_cache
def estado_presentacion_pitch(request, sesion_id):
    sesion = get_object_or_404(Sesion, pk=sesion_id)

    grupo_solicitante = obtener_grupo_desde_session(request)
    if grupo_solicitante and grupo_solicitante.sesion_id != sesion.idsesion:
        grupo_solicitante = None

    calcular_segundos_restantes(sesion)
    sesion.refresh_from_db()

    nombre_url = RUTA_POR_FASE.get(sesion.fase_actual, "pantalla_espera")

    data = {
        "ok": True,
        "faseActual": sesion.fase_actual,
        "rutaAlumno": reverse(nombre_url),
        **serializar_estado_pitch(sesion, grupo_solicitante=grupo_solicitante),
    }
    return JsonResponse(data)

@require_POST
def iniciar_presentacion_pitch(request, sesion_id):
    sesion = get_object_or_404(Sesion, pk=sesion_id)

    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return JsonResponse({
            "ok": False,
            "error": "No se pudo identificar tu grupo."
        }, status=403)

    if sesion.fase_actual != "f4_presentacion_pitch":
        return JsonResponse({
            "ok": False,
            "error": "La sesión no está en fase de presentación."
        }, status=400)

    grupo_actual = sesion.grupo_presentando
    if not grupo_actual:
        return JsonResponse({
            "ok": False,
            "error": "No hay un grupo asignado para presentar."
        }, status=400)

    if grupo.idgrupo != grupo_actual.idgrupo:
        return JsonResponse({
            "ok": False,
            "error": "Solo el grupo que está presentando puede iniciar el temporizador."
        }, status=403)

    segundos = int(sesion.segundos_restantes or sesion.t_pitch or 90)
    if segundos <= 0:
        segundos = int(sesion.t_pitch or 90)

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
        "faseActual": sesion.fase_actual,
        "rutaAlumno": reverse(RUTA_POR_FASE.get(sesion.fase_actual, "pantalla_espera")),
        **serializar_estado_pitch(sesion, grupo_solicitante=grupo),
    })


@require_POST
def siguiente_grupo_pitch(request, sesion_id):
    sesion = get_object_or_404(Sesion, pk=sesion_id)

    actual = sesion.grupo_presentando

    if actual is None:
        siguiente = Grupo.objects.filter(
            sesion=sesion,
            orden_presentacion__isnull=False
        ).order_by("orden_presentacion").first()
    else:
        siguiente = Grupo.objects.filter(
            sesion=sesion,
            orden_presentacion__gt=actual.orden_presentacion
        ).order_by("orden_presentacion").first()

    if siguiente is None:
        return JsonResponse({
            "ok": False,
            "error": "Ya no quedan más grupos por presentar."
        }, status=400)

    sesion.grupo_presentando = siguiente
    sesion.segundos_restantes = 90
    sesion.timer_corriendo = False
    sesion.save(update_fields=["grupo_presentando", "segundos_restantes", "timer_corriendo"])

    return JsonResponse({
        "ok": True,
        **serializar_estado_pitch(sesion),
    })

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

    grupos_data = [
        {
            "esProfesor": True,
            "id": g.idgrupo,
            "nombre": g.nombregrupo,
           "tokens": g.tokensgrupo or 0,
            "listoLobby": g.listo_lobby,
            "listoF1": g.listo_f1,
            "listoF2": g.listo_f2_desafio,
           "listoF2Generico": g.listo_f2,
            "listoF2Empatia": getattr(g, "listo_f2_empatia", False),
            "listoF3": g.listo_f3,
            "listoInicioF3": getattr(g, "listo_inicio_f3", False),
           "listoF3Lego": getattr(g, "listo_f3_lego", False),
           "legoSinFoto": getattr(g, "lego_sin_foto", False),
           "legoConFoto": bool(getattr(g, "foto_lego", None)) and getattr(g, "listo_f3_lego", False),
           "listoF4": g.listo_f4,
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

    grupos_listos_f5 = sum(1 for g in grupos_data if g["listoF5"])
    todos_listos_f5 = total_grupos > 0 and grupos_listos_f5 == total_grupos

    grupos_listos_f6 = sum(1 for g in grupos_data if g["listoF6"])
    todos_listos_f6 = total_grupos > 0 and grupos_listos_f6 == total_grupos

    grupos_listos_ranking = Grupo.objects.filter(sesion=sesion, listo_ranking=True).count()
    todos_listos_ranking = total_grupos > 0 and grupos_listos_ranking == total_grupos
    total_inicio, listos_inicio, todos_inicio = contar_listos_inicio_fase(sesion, sesion.fase_actual)


    pitch_data = {}
    if fase_actual in {"f4_orden_pitch", "f4_presentacion_pitch", "f5_evaluacion_pitch", "f6_ranking"}:
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

def evaluacion_actual_completa(sesion):
    grupo_actual = sesion.grupo_presentando
    if not grupo_actual:
        return False

    total_evaluadores = Grupo.objects.filter(sesion=sesion).exclude(pk=grupo_actual.pk).count()

    realizadas = Evaluacion.objects.filter(
        sesion=sesion,
        grupo_evaluado=grupo_actual
    ).exclude(
        grupo_evaluador=grupo_actual
    ).count()

    return total_evaluadores > 0 and realizadas >= total_evaluadores


def avanzar_al_siguiente_pitch_o_ranking(sesion):
    actual = sesion.grupo_presentando

    if actual is None:
        sesion.fase_actual = "f6_ranking"
        sesion.save(update_fields=["fase_actual"])
        return

    siguiente = Grupo.objects.filter(
        sesion=sesion,
        orden_presentacion__gt=actual.orden_presentacion
    ).order_by("orden_presentacion").first()

    if siguiente is None:
        sesion.fase_actual = "f6_ranking"
        sesion.grupo_presentando = None
        sesion.save(update_fields=["fase_actual", "grupo_presentando"])
        return

    sesion.grupo_presentando = siguiente
    sesion.fase_actual = "f4_presentacion_pitch"
    sesion.segundos_restantes = int(sesion.t_pitch or 90)
    sesion.timer_corriendo = False
    sesion.timer_inicio_at = None
    sesion.timer_fin_at = None
    sesion.inicio_fase_habilitado = True

    sesion.save(update_fields=[
        "grupo_presentando",
        "fase_actual",
        "segundos_restantes",
        "timer_corriendo",
        "timer_inicio_at",
        "timer_fin_at",
        "inicio_fase_habilitado",
    ])


@require_POST
def guardar_tematica(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return JsonResponse({"ok": False, "error": "Grupo no encontrado."}, status=403)

    if grupo.sesion.fase_actual != "f2_tematicas":
        return JsonResponse({"ok": False, "error": "La sesión no está en la etapa de temáticas."}, status=400)

    tema = ""

    if request.content_type and "application/json" in request.content_type:
        try:
            payload = json.loads(request.body or "{}")
            tema = (payload.get("tema") or payload.get("slug") or "").strip().lower()
        except Exception:
            tema = ""
    else:
        tema = (request.POST.get("tema") or request.POST.get("slug") or "").strip().lower()

    if not tema or not get_theme(tema):
        return JsonResponse({"ok": False, "error": "Tema no válido."}, status=400)

    grupo.tema_elegido = tema
    grupo.listo_f2_tematica = True
    grupo.desafio_elegido = None
    grupo.desafio_id_externo = None
    grupo.desafio_nombre = None
    grupo.desafio_descripcion = None
    grupo.listo_f2_desafio = False

    grupo.save(update_fields=[
        "tema_elegido",
        "listo_f2_tematica",
        "desafio_elegido",
        "desafio_id_externo",
        "desafio_nombre",
        "desafio_descripcion",
        "listo_f2_desafio",
    ])

    return JsonResponse({
        "ok": True,
        "redirect_url": reverse("desafios")
    })

@require_POST
def guardar_desafio(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return JsonResponse({"ok": False, "error": "Grupo no encontrado."}, status=403)

    if grupo.sesion.fase_actual != "f2_tematicas":
        return JsonResponse({"ok": False, "error": "La sesión no está en la etapa de desafíos."}, status=400)

    try:
        payload = json.loads(request.body or "{}")
        desafio_id = str(payload.get("desafio_id") or "").strip()
    except Exception:
        return JsonResponse({"ok": False, "error": "Solicitud inválida."}, status=400)

    if not desafio_id:
        return JsonResponse({"ok": False, "error": "Debes seleccionar un desafío."}, status=400)

    tema = (grupo.tema_elegido or "").strip().lower()
    theme = get_theme(tema)
    if not theme:
        return JsonResponse({"ok": False, "error": "Tema no válido."}, status=400)

    challenge = None
    for c in theme.get("challenges", []):
        if str(c.get("id")) == desafio_id:
            challenge = c
            break

    if not challenge:
        return JsonResponse({"ok": False, "error": "Desafío no válido."}, status=404)

    grupo.desafio_id_externo = str(challenge.get("id"))
    grupo.desafio_nombre = challenge.get("name", "")
    grupo.desafio_descripcion = challenge.get("desc", "")
    grupo.listo_f2_desafio = True

    grupo.save(update_fields=[
        "desafio_id_externo",
        "desafio_nombre",
        "desafio_descripcion",
        "listo_f2_desafio",
    ])

    return JsonResponse({
        "ok": True,
        "desafio_id": grupo.desafio_id_externo,
        "desafio_nombre": grupo.desafio_nombre,
        "desafio_descripcion": grupo.desafio_descripcion,
        "bloqueado": True,
    })

@require_POST
def desbloquear_desafio(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return JsonResponse({"ok": False, "error": "Grupo no encontrado."}, status=403)

    if grupo.sesion.fase_actual != "f2_tematicas":
        return JsonResponse({"ok": False, "error": "No puedes cambiar el desafío en esta etapa."}, status=400)

    grupo.listo_f2_desafio = False
    grupo.save(update_fields=["listo_f2_desafio"])

    return JsonResponse({"ok": True})

@require_POST
def profesor_actualizar_estado(request, sesion_id):
    sesion = get_object_or_404(Sesion, pk=sesion_id)
    payload = json.loads(request.body or "{}")

    fase_anterior = sesion.fase_actual
    nueva_fase = payload.get("faseActual")

    if nueva_fase:
        if nueva_fase not in FASES_ORDEN:
            return JsonResponse({"ok": False, "error": "Pantalla inválida"}, status=400)
        sesion.fase_actual = nueva_fase

    if nueva_fase and nueva_fase != fase_anterior:
        sesion.segundos_restantes = tiempo_por_fase(sesion, nueva_fase)
        sesion.timer_corriendo = False
        sesion.timer_inicio_at = None
        sesion.timer_fin_at = None

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

    if nueva_fase == "f6_ranking":
        total = Grupo.objects.filter(sesion=sesion).count()
        listos_ranking = Grupo.objects.filter(sesion=sesion, listo_ranking=True).count()

        if total == 0 or listos_ranking < total:
            return JsonResponse({
                "ok": False,
                "error": f"Aún faltan grupos por presionar Ranking final ({listos_ranking}/{total})."
            }, status=400)

    sesion.fase_actual = nueva_fase
    sesion.segundos_restantes = tiempo_por_fase(sesion, nueva_fase)
    sesion.timer_corriendo = False
    sesion.timer_inicio_at = None
    sesion.timer_fin_at = None

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
def marcar_listo_ranking(request, grupo_id):
    grupo = get_object_or_404(Grupo, pk=grupo_id)

    grupo.listo_ranking = True
    grupo.save(update_fields=["listo_ranking"])

    sesion = grupo.sesion
    total_grupos = Grupo.objects.filter(sesion=sesion).count()
    grupos_listos_ranking = Grupo.objects.filter(sesion=sesion, listo_ranking=True).count()


    return JsonResponse({
        "ok": True,
        "grupoId": grupo.idgrupo,
        "listoRanking": True,
        "gruposListosRanking": grupos_listos_ranking,
        "totalGrupos": total_grupos,
        "todosListosRanking": total_grupos > 0 and grupos_listos_ranking == total_grupos,
    })


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
            iniciar_timer_de_sesion(sesion)

        return JsonResponse({
            "ok": True,
            "fase": fase_actual,
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
            "total": total,
            "listos": listos,
            "gruposListos": listos,
            "totalGrupos": total,
            "todos_listos": todos,
        })

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
            "total": total,
            "listos": listos,
            "gruposListos": listos,
            "totalGrupos": total,
            "todos_listos": todos,
        })

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
            "total": total,
            "listos": listos,
            "gruposListos": listos,
            "totalGrupos": total,
            "todos_listos": todos,
        })

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
            "total": total,
            "listos": listos,
            "gruposListos": listos,
            "totalGrupos": total,
            "todos_listos": todos,
        })

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
            "total": total,
            "listos": listos,
            "gruposListos": listos,
            "totalGrupos": total,
            "todos_listos": todos,
        })

    if fase_actual == "f1_sopa":
        if not grupo.listo_f1:
            grupo.listo_f1 = True
            grupo.save(update_fields=["listo_f1"])

    elif fase_actual == "f2_bubblemap":
        if not grupo.listo_f2:
            grupo.listo_f2 = True
            grupo.save(update_fields=["listo_f2"])

    elif fase_actual == "f3_lego":
        if not grupo.listo_inicio_f3:
            grupo.listo_inicio_f3 = True
            grupo.save(update_fields=["listo_inicio_f3"])

    elif fase_actual == "f4_construccion_pitch":
        if not grupo.listo_f4:
            grupo.listo_f4 = True
            grupo.save(update_fields=["listo_f4"])

    else:
        return JsonResponse({
            "ok": False,
            "error": f"La fase actual '{fase_actual}' no usa inicio grupal.",
        }, status=400)

    total, listos, todos = contar_listos_inicio_fase(sesion, fase_actual)

    if todos and not sesion.inicio_fase_habilitado:
        sesion.inicio_fase_habilitado = True
        sesion.save(update_fields=["inicio_fase_habilitado"])
        iniciar_timer_de_sesion(sesion)

    return JsonResponse({
        "ok": True,
        "fase": fase_actual,
        "total": total,
        "listos": listos,
        "gruposListos": listos,
        "totalGrupos": total,
        "todos_listos": todos,
        "inicio_fase_habilitado": sesion.inicio_fase_habilitado,
    })


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


def pantalla_inicio(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")
    if not acceso_permitido(grupo, "pantalla_inicio"):
        return redirect("pantalla_espera")
    return render(request, "pantalla_inicio.html", {"grupo": grupo})


def trabajoenequipo(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")
    if not acceso_permitido(grupo, "trabajoenequipo"):
        return redirect("pantalla_espera")
    return render(request, "trabajoenequipo.html", {"grupo": grupo})

@never_cache
def tematicas(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")

    if not acceso_permitido(grupo, "tematicas"):
        return redirect("pantalla_espera")

    if (grupo.tema_elegido or "").strip():
        return redirect("desafios")

    return render(request, "tematicas.html", {
        "grupo": grupo,
        "tema_actual": (grupo.tema_elegido or "").strip().lower(),
    })

    print(f"tematicas -> grupo actual: {grupo.idgrupo} | nombre: {grupo.nombregrupo} | sesion: {grupo.sesion.idsesion}")

    if not acceso_permitido(grupo, "tematicas"):
        print(f"tematicas -> acceso no permitido para grupo {grupo.idgrupo}")
        return redirect("pantalla_espera")

    return render(request, "tematicas.html", {"grupo": grupo})

@never_cache
def lego(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")

    if not acceso_permitido(grupo, "lego"):
        return redirect("pantalla_espera")

    sesion = grupo.sesion

    if request.method == "POST":
        sin_foto = request.POST.get("sin_foto_lego") == "on"
        foto = request.FILES.get("foto_lego")

        if sin_foto:
            grupo.foto_lego = None
            grupo.listo_f3_lego = True
            grupo.lego_sin_foto = True
            grupo.save(update_fields=["foto_lego", "listo_f3_lego", "lego_sin_foto"])

        elif foto:
            grupo.foto_lego = foto
            grupo.listo_f3_lego = True
            grupo.lego_sin_foto = False
            grupo.save(update_fields=["foto_lego", "listo_f3_lego", "lego_sin_foto"])

        else:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({
                    "ok": False,
                    "error": "Debes subir una foto o marcar que no pudieron subirla."
                }, status=400)

            messages.error(request, "Debes subir una foto o marcar que no pudieron subirla.")
            return render(request, "lego.html", {
                "grupo": grupo,
                "desafio_nombre_actual": grupo.desafio_nombre or "Desafío no seleccionado",
                "desafio_descripcion_actual": grupo.desafio_descripcion or "Aún no hay descripción disponible para este desafío.",
                "tiempo_inicial_lego": grupo.sesion.segundos_restantes or 15,
            })

        autoavanzar_si_todos_listos(sesion)
        sesion.refresh_from_db()

        total_grupos = Grupo.objects.filter(sesion=sesion).count()
        grupos_listos = Grupo.objects.filter(sesion=sesion, listo_f3_lego=True).count()
        grupos_con_foto = Grupo.objects.filter(sesion=sesion, listo_f3_lego=True, foto_lego__isnull=False).count()
        grupos_sin_foto = Grupo.objects.filter(sesion=sesion, listo_f3_lego=True, lego_sin_foto=True).count()

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({
                "ok": True,
                "gruposListosF3Lego": grupos_listos,
                "gruposConFotoLego": grupos_con_foto,
                "gruposSinFotoLego": grupos_sin_foto,
                "totalGrupos": total_grupos,
                "todosListosF3Lego": total_grupos > 0 and grupos_listos == total_grupos,
                "faseActual": sesion.fase_actual,
                "rutaAlumno": reverse(RUTA_POR_FASE.get(sesion.fase_actual, "pantalla_espera")),
            })

        return redirect("lego")

    return render(request, "lego.html", {
        "grupo": grupo,
        "desafio_nombre_actual": grupo.desafio_nombre or "Desafío no seleccionado",
        "desafio_descripcion_actual": grupo.desafio_descripcion or "Aún no hay descripción disponible para este desafío.",
        "tiempo_inicial_lego": grupo.sesion.segundos_restantes or 15,
    })


#NUEVO CIERRRE
def perfiles(request):
    return render(request, 'perfiles.html')


def bienvenida(request):
    return render(request, 'bienvenida.html')


def registro(request):
    error = None

    if request.method == "POST":
        codigo = (request.POST.get("id_grupo") or "").strip().upper()

        if not codigo:
            error = "Debes ingresar un código."
            return render(request, "registro.html", {"error": error})

        try:
            grupo = Grupo.objects.select_related("sesion").get(codigoacceso__iexact=codigo)
        except Grupo.DoesNotExist:
            error = "Código de grupo inválido"
            return render(request, "registro.html", {"error": error})

        request.session.flush()
        request.session.cycle_key()
        request.session["grupo_id"] = grupo.idgrupo
        request.session["sesion_id"] = grupo.sesion_id
        request.session["ranking_flags_reseteados"] = False
        request.session.modified = True

        print(f"registro -> codigo={codigo} | grupo={grupo.idgrupo} | nombre={grupo.nombregrupo} | sesion={grupo.sesion.idsesion if grupo.sesion else 'SIN SESION'}")

        return redirect("pantalla_inicio")

    return render(request, "registro.html", {"error": error})




def introducciones(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")
    if not acceso_permitido(grupo, "introducciones"):
        return redirect("pantalla_espera")
    return render(request, "introducciones.html", {"grupo": grupo})

def promptconocidos(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")
    if not acceso_permitido(grupo, "promptconocidos"):
        return redirect("pantalla_espera")
    return render(request, "promptconocidos.html", {"grupo": grupo})

def conocidos(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")
    if not acceso_permitido(grupo, "conocidos"):
        return redirect("pantalla_espera")
    return render(request, "conocidos.html", {"grupo": grupo})

def minijuego1(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")
    if not acceso_permitido(grupo, "minijuego1"):
        return redirect("pantalla_espera")
    return render(request, "minijuego1.html", {
        "grupo": grupo,
        "sopa_ganada": bool(grupo.sopa_ganada),
    })

@require_POST
def sopa_completada(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return JsonResponse({"ok": False, "error": "No se pudo identificar tu grupo."}, status=403)

    with transaction.atomic():
        grupo = Grupo.objects.select_for_update().get(pk=grupo.pk)

        if grupo.sopa_ganada:
            return JsonResponse({"ok": True, "ya_completada": True})

        ya_habia_otro = Grupo.objects.select_for_update().filter(
            sesion=grupo.sesion,
            sopa_ganada=True
        ).exclude(pk=grupo.pk).exists()

        bonus = 3
        if not ya_habia_otro:
            bonus += 2

        grupo.tokensgrupo = (grupo.tokensgrupo or 0) + bonus
        grupo.sopa_ganada = True
        grupo.save(update_fields=["tokensgrupo", "sopa_ganada"])

    return JsonResponse({
        "ok": True,
        "bonus_otorgado": bonus,
        "primer_equipo": not ya_habia_otro,
    })

@require_POST
def registrar_palabra_sopa(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return JsonResponse({"ok": False, "error": "No se pudo identificar tu grupo."}, status=403)

    try:
        payload = json.loads(request.body or "{}")
    except Exception:
        payload = {}

    palabra = (payload.get("palabra") or "").strip().upper()
    if not palabra:
        return JsonResponse({"ok": False, "error": "Palabra inválida."}, status=400)

    with transaction.atomic():
        _, creada = PalabraSopaEncontrada.objects.get_or_create(
            sesion=grupo.sesion,
            grupo=grupo,
            palabra=palabra,
        )

        if creada:
            Grupo.objects.filter(pk=grupo.pk).update(tokensgrupo=F("tokensgrupo") + 1)

    return JsonResponse({
        "ok": True,
        "nueva": creada,
    })

def dashboardprofesor(request):
    profesor = Profesor.objects.first()
    sesion = None

    if profesor:
        sesion = Sesion.objects.filter(profesor=profesor).order_by("-fecha_creacion").first()

    return render(request, "dashboardprofesor.html", {"sesion": sesion})

def control_sesion(request, sesion_id):
    sesion = get_object_or_404(Sesion, pk=sesion_id)
    grupos = Grupo.objects.filter(sesion=sesion).order_by("idgrupo")

    return render(request, "control_sesion.html", {
        "sesion": sesion,
        "grupos": grupos,
        "es_profesor_panel": True,
    })

def dashboardadmin(request):
    return render(request, 'dashboardadmin.html')


def agregardesafio(request):

    admin = Idadministrador.objects.first()

    if request.method == "POST":
        nombre = request.POST.get("nombre")
        descripcion = request.POST.get("descripcion")
        tokens = request.POST.get("tokens")

        if not nombre or not tokens:
            messages.error(request, "Debes ingresar nombre y tokens.")
            return redirect("agregardesafio")

        Desafio.objects.create(
            idadministrador_idadministrador=admin,
            nombredesafio=nombre,
            descripciondesafio=descripcion,
            tokensdesafio=int(tokens)
        )

        messages.success(request, "Desafío creado correctamente")
        return redirect("agregardesafio")
    
    return render(request, 'agregardesafio.html')

def lista_desafios(request):
    desafios = Desafio.objects.all().order_by('iddesafio')
    return render(request, 'listadesafios.html', {
        'desafios': desafios,
    })


def eliminar_desafio(request, iddesafio):
    desafio = get_object_or_404(Desafio, pk=iddesafio)

    if request.method == "POST":
        desafio.delete()
        messages.success(request, "Desafío eliminado correctamente 🗑️")
        return redirect('lista_desafios')

    return redirect('lista_desafios')

def transicionempatia(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")
    if not acceso_permitido(grupo, "transicionempatia"):
        return redirect("pantalla_espera")
    return render(request, "transicionempatia.html", {"grupo": grupo})


def transicioncreatividad(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")
    if not acceso_permitido(grupo, "transicioncreatividad"):
        return redirect("pantalla_espera")
    return render(request, "transicioncreatividad.html", {"grupo": grupo})

def transicioncomunicacion(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")
    if not acceso_permitido(grupo, "transicioncomunicacion"):
        return redirect("pantalla_espera")
    return render(request, "transicioncomunicacion.html", {"grupo": grupo})


def transiciondesafio(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")
    if not acceso_permitido(grupo, "transiciondesafio"):
        return redirect("pantalla_espera")
    return render(request, "transiciondesafio.html", {"grupo": grupo})


def transicionapoyo(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")
    if not acceso_permitido(grupo, "transicionapoyo"):
        return redirect("pantalla_espera")
    return render(request, "transicionapoyo.html", {"grupo": grupo})

@transaction.atomic
def asignar_alumnos_a_grupos(sesion: Sesion):

    alumnos = list(
        Alumno.objects.filter(sesion=sesion, grupo__isnull=True)
        .order_by('idalumno')
    )

    if not alumnos:
        print("No hay alumnos sin grupo en esta sesión.")
        return 0

    grupos = list(Grupo.objects.filter(sesion=sesion).order_by('idgrupo'))

    if not grupos:
        n_alumnos = len(alumnos)
        num_grupos = ceil(n_alumnos / 8)

        for i in range(num_grupos):
            grupos.append(
                Grupo.objects.create(
                    sesion=sesion,
                    nombregrupo=f"Grupo {i+1}",
                    usuario_idusuario=None,
                    tokensgrupo=10,
                    etapa=1,
                    codigoacceso=generar_codigo_acceso(),
                )
            )
    else:
        for g in grupos:
            if not g.codigoacceso:
                g.codigoacceso = generar_codigo_acceso()
                g.save()

    n_alumnos = len(alumnos)
    n_grupos = len(grupos)

    capacidad_base = n_alumnos // n_grupos
    sobrantes = n_alumnos % n_grupos

    index_alumno = 0

    for i, grupo in enumerate(grupos):
        cantidad = capacidad_base + (1 if i < sobrantes else 0)

        for _ in range(cantidad):
            if index_alumno >= n_alumnos:
                break

            alumno = alumnos[index_alumno]
            alumno.grupo = grupo
            alumno.save()
            index_alumno += 1

    print(f"Asignados {index_alumno} alumnos en sesión {sesion.idsesion}")
    return index_alumno


def registrargrupos(request):
    profesor = Profesor.objects.first()

    if not profesor:
        messages.warning(
            request,
            "Primero debes registrar un profesor."
        )
        return redirect("registrarprofesor")

    sesion_activa = (
        Sesion.objects.filter(profesor=profesor)
        .order_by('-fecha_creacion')
        .first()
    )

    if not sesion_activa:
        messages.warning(
            request,
            "Aún no tienes sesiones creadas. Primero crea una sesión."
        )
        return redirect('crear_sesion')

    if request.method == "POST":
        cantidad = asignar_alumnos_a_grupos(sesion_activa)
        if cantidad == 0:
            messages.info(request, "No había alumnos sin grupo en esta sesión.")
        else:
            messages.success(
                request,
                f"Alumnos auto-asignados correctamente en la sesión '{sesion_activa.nombre}'."
            )
        return redirect("registrargrupos")

    grupos = (
        Grupo.objects
        .filter(sesion=sesion_activa)
        .prefetch_related("alumno_set")
        .order_by('idgrupo')
    )

    context = {
        "grupos": grupos,
        "sesion_activa": sesion_activa,
    }
    return render(request, "registrargrupos.html", context)


def generar_codigo_acceso(longitud=6):
    caracteres = string.ascii_uppercase + string.digits
    while True:
        codigo = ''.join(random.choices(caracteres, k=longitud))
        if not Grupo.objects.filter(codigoacceso=codigo).exists():
            return codigo

def cargar_alumnos(request):
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
        messages.warning(request, "Primero crea una sesión antes de cargar alumnos.")
        return redirect("crear_sesion")

    alumnos = (
        Alumno.objects.filter(profesor_idprofesor=profesor, sesion=sesion_activa)
        .order_by('idalumno')
    )

    if request.method == "POST" and request.FILES.get("archivo_excel"):
        archivo = request.FILES["archivo_excel"]

        try:
            if archivo.name.lower().endswith('.xlsx'):
                df = pd.read_excel(archivo)
            elif archivo.name.lower().endswith('.csv'):
                df = pd.read_csv(archivo)
            else:
                messages.error(request, "Formato no soportado. Usa .xlsx o .csv.")
                return render(
                    request,
                    "registraralumnos.html",
                    {"alumnos": alumnos, "sesion_activa": sesion_activa},
                )

            with transaction.atomic():
                for _, row in df.iterrows():
                    Alumno.objects.create(
                        profesor_idprofesor=profesor,
                        sesion=sesion_activa,
                        emailalumno=row.get('Correo'),
                        rutalumno=row.get('RUT'),
                        nombrealumno=row.get('Nombre'),
                        apellidopaternoalumno=row.get('Apellido Paterno'),
                        apellidomaternoalumno=row.get('Apellido Materno'),
                        carreraalumno=row.get('Carrera', ''),  # opcional
                    )

            messages.success(
                request,
                f"Alumnos cargados correctamente para la sesión '{sesion_activa.nombre}'."
            )

            alumnos = (
                Alumno.objects.filter(profesor_idprofesor=profesor, sesion=sesion_activa)
                .order_by('idalumno')
            )

        except Exception as e:
            messages.error(request, f"Error al leer el archivo: {e}")

    return render(
        request,
        "registraralumnos.html",
        {"alumnos": alumnos, "sesion_activa": sesion_activa},
    )


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

@never_cache
def desafios(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")

    if not acceso_permitido(grupo, "desafios"):
        return redirect("pantalla_espera")

    slug = (grupo.tema_elegido or "").strip().lower()
    if not slug:
        return redirect("tematicas")

    theme = get_theme(slug)
    if not theme:
        return redirect("tematicas")

    return render(request, "desafios.html", {
        "grupo": grupo,
        "theme": theme,
        "slug": slug,
        "desafio_confirmado": bool(grupo.listo_f2_desafio),
        "desafio_id_actual": str(grupo.desafio_id_externo or ""),
        "desafio_nombre_actual": grupo.desafio_nombre or "",
        "desafio_descripcion_actual": grupo.desafio_descripcion or "",
    })





@never_cache
def bubblemap(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")

    if not acceso_permitido(grupo, "bubblemap"):
        return redirect("pantalla_espera")

    sesion = grupo.sesion

    desafio_id = request.GET.get("desafio")

    if desafio_id:
        request.session["desafio_id"] = desafio_id
        request.session["desafio_nombre"] = grupo.desafio_nombre
        request.session["desafio_descripcion"] = getattr(grupo, "desafio_descripcion", "") or ""
        request.session.modified = True

    desafio_nombre = (
        grupo.desafio_nombre
        or request.session.get("desafio_nombre")
        or "Desafío no seleccionado"
    )

    desafio_descripcion = (
        getattr(grupo, "desafio_descripcion", None)
        or request.session.get("desafio_descripcion")
        or "Aún no hay descripción disponible para este desafío."
    )

    segundos = 180
    if sesion and sesion.segundos_restantes is not None:
        segundos = sesion.segundos_restantes

    return render(request, "bubblemap.html", {
        "grupo": grupo,
        "sesion": sesion,
        "desafio_nombre_actual": desafio_nombre,
        "desafio_descripcion_actual": desafio_descripcion,
        "segundos_restantes": segundos,
    })
def orden_presentacion_alumno(request):
    grupo = obtener_grupo_desde_session(request)

    if not grupo:
        return redirect("registro")

    if not acceso_permitido(grupo, "orden_presentacion_alumno"):
        return redirect("pantalla_espera")

    grupos_ordenados = Grupo.objects.filter(
        sesion=grupo.sesion
    ).exclude(
        orden_presentacion__isnull=True
    ).order_by("orden_presentacion")

    return render(request, "orden_presentacion.html", {
        "grupo": grupo,
        "grupos_ordenados": grupos_ordenados,
    })

@never_cache
def pitch(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")

    if not acceso_permitido(grupo, "pitch"):
        return redirect("pantalla_espera")

    return render(request, "pitch.html", {
        "grupo": grupo,
        "pitch_guardado": grupo.pitch_texto or "",
        "desafio_nombre_actual": grupo.desafio_nombre or "Desafío no seleccionado",
        "desafio_descripcion_actual": grupo.desafio_descripcion or "Aún no hay descripción disponible para este desafío.",
    })


@require_POST
def guardar_pitch(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return JsonResponse({"ok": False, "error": "Grupo no encontrado."}, status=401)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"ok": False, "error": "JSON inválido."}, status=400)

    texto = (data.get("pitch_texto") or "").strip()

    grupo.pitch_texto = texto
    grupo.save(update_fields=["pitch_texto"])

    return JsonResponse({
        "ok": True,
        "pitch_texto": grupo.pitch_texto or "",
    })


@require_POST
def profesor_sortear_orden_pitch(request, sesion_id):
    sesion = get_object_or_404(Sesion, pk=sesion_id)

    grupos = list(Grupo.objects.filter(sesion=sesion).order_by("idgrupo"))
    if not grupos:
        return JsonResponse({"ok": False, "error": "No hay grupos en la sesión."}, status=400)

    random.shuffle(grupos)

    for i, grupo in enumerate(grupos, start=1):
        grupo.orden_presentacion = i
        grupo.save(update_fields=["orden_presentacion"])

    primer_grupo = sorted(grupos, key=lambda g: g.orden_presentacion)[0]

    sesion.grupo_presentando = primer_grupo
    sesion.segundos_restantes = int(sesion.t_pitch or 90)
    sesion.timer_corriendo = False
    sesion.timer_inicio_at = None
    sesion.timer_fin_at = None
    sesion.inicio_fase_habilitado = True
    sesion.save(update_fields=[
        "grupo_presentando",
        "segundos_restantes",
        "timer_corriendo",
        "timer_inicio_at",
        "timer_fin_at",
        "inicio_fase_habilitado",
    ])

    return JsonResponse({
        "ok": True,
        "orden": [
            {
                "id": g.idgrupo,
                "nombre": g.nombregrupo,
                "orden": g.orden_presentacion,
            }
            for g in sorted(grupos, key=lambda x: x.orden_presentacion)
        ],
        **serializar_estado_pitch(sesion),
    })

@never_cache
def presentar_pitch(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")

    if not acceso_permitido(grupo, "presentar_pitch"):
        return redirect("pantalla_espera")

    return render(request, "presentar_pitch.html", {
        "grupo": grupo,
        "miPitch": grupo.pitch_texto or "",
    })


def registraralumnos(request):
    return cargar_alumnos(request)

def market_view(request):
    grupo_id = request.session.get("grupo_id")
    if not grupo_id:
        messages.error(request, "No se encontró el grupo asociado a esta sesión.")
        return redirect("registro")

    grupo_actual = get_object_or_404(Grupo, pk=grupo_id)

    user_tokens = grupo_actual.tokensgrupo or 0

    challenges = Reto.objects.all()

    other_teams = Grupo.objects.filter(
        sesion=grupo_actual.sesion
    ).exclude(pk=grupo_actual.pk)

    context = {
        "user_tokens": user_tokens,
        "challenges": challenges,
        "other_teams": other_teams,
    }
    return render(request, "market.html", context)

@require_http_methods(["POST"])
def issue_challenge_view(request, challenge_id):
    grupo_id = request.session.get("grupo_id")
    if not grupo_id:
        messages.error(request, "No se encontró el grupo asociado a esta sesión.")
        return redirect("market")

    grupo_emisor = get_object_or_404(Grupo, pk=grupo_id)

    reto = get_object_or_404(Reto, pk=challenge_id)

    target_team_id = request.POST.get("target_team_id")
    if not target_team_id:
        messages.error(request, "Selecciona un equipo objetivo.")
        return redirect("market")

    grupo_receptor = get_object_or_404(Grupo, pk=target_team_id)

    cost = int(reto.costoreto or 0)

    if cost < 0:
        messages.error(request, "El costo del reto no puede ser negativo.")
        return redirect("market")

    saldo_actual = grupo_emisor.tokensgrupo or 0
    if saldo_actual < cost:
        messages.error(request, "No tienes tokens suficientes para enviar este reto.")
        return redirect("market")

    if cost > 0:
        grupo_emisor.ajustar_tokens(-cost)

    desafio = reto.desafio_iddesafio
    recompensa = (desafio.tokensdesafio or 0) if desafio else 0

    if recompensa <= 0:
        recompensa = cost

    penalizacion = recompensa

    Retogrupo.objects.create(
        reto=reto,
        grupo_emisor=grupo_emisor,
        grupo_receptor=grupo_receptor,
        tokens_costo=cost,
        tokens_recompensa=recompensa,
        tokens_penalizacion=penalizacion,
        fecha_creacion=timezone.now()
    )

    nuevo_saldo = (grupo_emisor.tokensgrupo or 0)

    messages.success(
        request,
        f"Has retado al equipo {grupo_receptor.nombregrupo} con “{reto.nombrereto}” "
        f"por {cost} tokens. Te quedan ahora {nuevo_saldo} tokens."
    )
    return redirect("market")

@never_cache
def peer_review_view(request):
    grupo_evaluador = obtener_grupo_desde_session(request)
    if not grupo_evaluador:
        return redirect("registro")

    if not acceso_permitido(grupo_evaluador, "peer_review"):
        return redirect("pantalla_espera")

    sesion = grupo_evaluador.sesion
    grupo_objetivo = sesion.grupo_presentando

    if not grupo_objetivo:
        return redirect("pantalla_espera")

    criteria = [
        {"key": "claridad", "label": "Claridad"},
        {"key": "creatividad", "label": "Creatividad"},
        {"key": "viabilidad", "label": "Viabilidad"},
        {"key": "equipo", "label": "Trabajo en equipo"},
        {"key": "presentacion", "label": "Presentación"},
    ]

    if grupo_evaluador.pk == grupo_objetivo.pk:
        if evaluacion_actual_completa(sesion):
            avanzar_al_siguiente_pitch_o_ranking(sesion)
            return redirect("pantalla_espera")

        return render(request, "peer_review.html", {
            "session": sesion,
            "evaluator_team": grupo_evaluador,
            "grupo_objetivo": grupo_objetivo,
            "mi_equipo_presenta": True,
            "ya_evaluo": False,
            "criteria": criteria,
        })

    ya_evaluo = Evaluacion.objects.filter(
        sesion=sesion,
        grupo_evaluador=grupo_evaluador,
        grupo_evaluado=grupo_objetivo,
    ).exists()

    if request.method == "POST":
        if ya_evaluo:
            if evaluacion_actual_completa(sesion):
                avanzar_al_siguiente_pitch_o_ranking(sesion)
            return redirect("pantalla_espera")

        claridad = int(request.POST.get("score_claridad", 0))
        creatividad = int(request.POST.get("score_creatividad", 0))
        viabilidad = int(request.POST.get("score_viabilidad", 0))
        equipo = int(request.POST.get("score_equipo", 0))
        presentacion = int(request.POST.get("score_presentacion", 0))
        comentario = (request.POST.get("comment") or "").strip()
        reflexion = (request.POST.get("reflection") or "").strip()

        Evaluacion.objects.create(
            sesion=sesion,
            grupo_evaluador=grupo_evaluador,
            grupo_evaluado=grupo_objetivo,
            claridad=claridad,
            creatividad=creatividad,
            viabilidad=viabilidad,
            equipo=equipo,
            presentacion=presentacion,
            comentario=comentario,
            reflexion=reflexion or None,
        )

        grupo_evaluador.listo_f5 = True
        grupo_evaluador.save(update_fields=["listo_f5"])

        if evaluacion_actual_completa(sesion):
            avanzar_al_siguiente_pitch_o_ranking(sesion)

        return redirect("pantalla_espera")

    return render(request, "peer_review.html", {
        "session": sesion,
        "evaluator_team": grupo_evaluador,
        "grupo_objetivo": grupo_objetivo,
        "mi_equipo_presenta": False,
        "ya_evaluo": ya_evaluo,
        "criteria": criteria,
    })



def ranking(request):
    return render(request, 'ranking.html')

def registrarprofesor(request):
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip()
        facultad = (request.POST.get("facultad") or "").strip()

        if not email or not facultad:
            messages.error(request, "Completa todos los campos obligatorios.")
            return render(request, "registrarprofesor.html")

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "El correo no es válido.")
            return render(request, "registrarprofesor.html")

        if Profesor.objects.filter(emailprofesor=email).exists():
            messages.warning(request, "Ya existe un profesor con ese correo.")
            return render(request, "registrarprofesor.html")

        try:
            with transaction.atomic():
                tmp_password = secrets.token_urlsafe(8)
                usuario = Usuario.objects.create(password=tmp_password)
                profesor = Profesor.objects.create(
                    usuario_idusuario=usuario,
                    emailprofesor=email,
                    facultad=facultad
                )

            messages.success(
                request,
                f"Profesor creado (ID {profesor.idprofesor}). Usuario ID {usuario.idusuario} asignado."
            )
            return redirect("dashboardadmin")

        except Exception as e:
            messages.error(request, f"Ocurrió un error al guardar: {e}")
            return render(request, "registrarprofesor.html")

    return render(request, "registrarprofesor.html")


def listar_profesores(request):
    profesores = Profesor.objects.all().order_by('-idprofesor')
    return render(request, 'listar_profesores.html', {'profesores': profesores})

@require_http_methods(["POST"])
def eliminar_profesor(request, idprofesor):
    profesor = get_object_or_404(Profesor, idprofesor=idprofesor)

    if Alumno.objects.filter(profesor_idprofesor=profesor).exists():
        messages.error(request, "No se puede eliminar: el profesor tiene alumnos asociados.")
        return redirect('listar_profesores')

    try:
        with transaction.atomic():
            usuario = profesor.usuario_idusuario
            profesor.delete()
            if not Profesor.objects.filter(usuario_idusuario=usuario).exists():
                usuario.delete()

        messages.success(request, "Profesor eliminado correctamente.")
    except Exception as e:
        messages.error(request, f"Error al eliminar: {e}")

    return redirect('listar_profesores')

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

def finalizar_mision(request):
    request.session.pop("grupo_id", None)
    return redirect("perfiles")

def reflexion(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")

    if not acceso_permitido(grupo, "reflexion"):
        return redirect("pantalla_espera")

    return render(request, "reflexion.html", {"grupo": grupo})

def crear_sesion(request):
    profesor = Profesor.objects.first()

    if not profesor:
        messages.warning(request, "Primero debes registrar un profesor.")
        return redirect("registrarprofesor")

    if request.method == "POST":
        nombre = (request.POST.get("nombre") or "").strip()

        if not nombre:
            messages.error(request, "Debes darle un nombre a la sesión.")
            return render(request, "crear_sesion.html")

        Sesion.objects.create(
            profesor=profesor,
            nombre=nombre,
            fase_actual="f1_bienvenida",
            timer_corriendo=False,
            segundos_restantes=0
        )

        messages.success(request, "Sesión creada correctamente.")
        return redirect("listar_sesiones")

    return render(request, "crear_sesion.html")


def listar_sesiones(request):
    profesor = Profesor.objects.first()

    if not profesor:
        messages.warning(request, "Aún no hay profesores registrados.")
        return redirect("registrarprofesor")

    sesiones = Sesion.objects.filter(profesor=profesor).order_by('-fecha_creacion')
    return render(request, "listar_sesiones.html", {"sesiones": sesiones})

def otorgar_tokens_peer_review(grupo_evaluador: Grupo):

    if getattr(grupo_evaluador, "recompensa_peer_otorgada", False):
        return

    sesion = grupo_evaluador.sesion
    if not sesion:
        return

    qs = (
        Evaluacion.objects
        .filter(sesion=sesion, grupo_evaluador=grupo_evaluador)
        .annotate(
            total=(
                F("claridad")
                + F("creatividad")
                + F("viabilidad")
                + F("equipo")
                + F("presentacion")
            )
        )
        .order_by("-total", "grupo_evaluado_id")
    )

    if not qs.exists():
        return

    mejor_eval = qs.first()
    grupo_premiado = mejor_eval.grupo_evaluado

    grupo_premiado.tokensgrupo = (grupo_premiado.tokensgrupo or 0) + 2
    grupo_premiado.save()

    grupo_evaluador.recompensa_peer_otorgada = True
    grupo_evaluador.save()


def ranking_view(request):
    grupo_id = request.session.get("grupo_id")
    if not grupo_id:
        messages.error(request, "No pudimos identificar tu grupo.")
        return redirect("registro")

    grupo_actual = get_object_or_404(Grupo, pk=grupo_id)
    sesion = grupo_actual.sesion

    if not sesion:
        messages.error(request, "Tu grupo no está asociado a ninguna sesión.")
        return redirect("registro")

    grupos = (
        Grupo.objects
        .filter(sesion=sesion)
        .order_by("-tokensgrupo", "idgrupo")
    )

    rankings = []
    last_tokens = None
    current_rank = 0
    position = 0

    for g in grupos:
        position += 1
        tokens = g.tokensgrupo or 0

        if tokens != last_tokens:
            current_rank = position
            last_tokens = tokens

        rankings.append({
            "team_name": g.nombregrupo or f"Grupo {g.idgrupo}",
            "tokens": tokens,
            "is_me": g.idgrupo == grupo_actual.idgrupo,
            "rank": current_rank,
        })

    context = {
        "session": sesion,
        "grupo": grupo_actual,
        "rankings": rankings,
    }
    return render(request, "ranking.html", context)

@never_cache
def mision_cumplida_view(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        messages.error(request, "No pudimos identificar tu grupo.")
        return redirect("registro")

    if not acceso_permitido(grupo, "mision_cumplida"):
        return redirect("pantalla_espera")

    if not peer_review_completado(grupo):
        return redirect("peer_review")

    return render(request, "mision_cumplida.html", {
        "grupo": grupo,
    })

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