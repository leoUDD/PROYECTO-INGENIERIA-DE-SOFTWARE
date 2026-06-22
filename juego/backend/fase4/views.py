import json
from datetime import timedelta

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone

from juego.models import Grupo, Sesion, Evaluacion

from juego.backend.core_global.services import (
    acceso_permitido,
    obtener_grupo_desde_session,
    calcular_segundos_restantes,
    autoavanzar_si_todos_listos,
    RUTA_POR_FASE,
)

from juego.backend.fase4.services import serializar_estado_pitch

def transicioncomunicacion(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")
    if not acceso_permitido(grupo, "transicioncomunicacion"):
        return redirect("pantalla_espera")
    return render(request, "fase4/transicioncomunicacion.html", {"grupo": grupo})

@never_cache
def pitch(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")

    if not acceso_permitido(grupo, "pitch"):
        return redirect("pantalla_espera")

    grupo.refresh_from_db()

    return render(request, "fase4/pitch.html", {
        "grupo": grupo,
        "pitch_guardado": grupo.pitch_texto or "",
        "desafio_nombre_actual": grupo.desafio_nombre or "Desafío no seleccionado",
        "desafio_descripcion_actual": grupo.desafio_descripcion or "Aún no hay descripción disponible para este desafío.",
    })


@require_POST
def guardar_pitch(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return JsonResponse({"ok": False, "error": "Grupo no encontrado."}, status=403)

    try:
        payload = json.loads(request.body or "{}")
    except Exception:
        payload = {}

    pitch_texto = (payload.get("pitch") or "").strip()

    grupo.pitch_texto = pitch_texto
    grupo.save(update_fields=["pitch_texto"])

    return JsonResponse({
        "ok": True,
        "pitch": grupo.pitch_texto,
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

    return render(request, "fase4/orden_presentacion.html", {
        "grupo": grupo,
        "grupos_ordenados": grupos_ordenados,
    })

@require_GET
@never_cache
def estado_presentacion_pitch(request, sesion_id):
    sesion = get_object_or_404(Sesion, pk=sesion_id)

    grupo_solicitante = obtener_grupo_desde_session(request)
    if grupo_solicitante and grupo_solicitante.sesion_id != sesion.idsesion:
        grupo_solicitante = None

    calcular_segundos_restantes(sesion)
    autoavanzar_si_todos_listos(sesion)
    sesion.refresh_from_db()

    nombre_url = RUTA_POR_FASE.get(sesion.fase_actual, "pantalla_espera")

    grupos = Grupo.objects.filter(sesion=sesion).order_by("idgrupo")

    grupos_data = [
        {
            "id": g.idgrupo,
            "nombre": g.nombregrupo,
            "listoF4Orden": getattr(g, "listo_f4_orden", False),
        }
        for g in grupos
    ]

    total_grupos = len(grupos_data)
    grupos_listos_f4_orden = sum(1 for g in grupos_data if g["listoF4Orden"])
    todos_listos_f4_orden = total_grupos > 0 and grupos_listos_f4_orden == total_grupos

    data = {
        "ok": True,
        "faseActual": sesion.fase_actual,
        "rutaAlumno": reverse(nombre_url),
        "totalGrupos": total_grupos,
        "grupos": grupos_data,
        "gruposListosF4Orden": grupos_listos_f4_orden,
        "todosListosF4Orden": todos_listos_f4_orden,
        **serializar_estado_pitch(sesion, grupo_solicitante=grupo_solicitante),
    }
    return JsonResponse(data)

@never_cache
def presentar_pitch(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")

    if not acceso_permitido(grupo, "presentar_pitch"):
        return redirect("pantalla_espera")

    return render(request, "fase4/presentar_pitch.html", {
        "grupo": grupo,
        "miPitch": grupo.pitch_texto or "",
    })

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

        otorgar_tokens_peer_review(grupo_evaluador)

        grupo_evaluador.listo_f5 = True
        grupo_evaluador.save(update_fields=["listo_f5"])

        if evaluacion_actual_completa(sesion):
            avanzar_al_siguiente_pitch_o_ranking(sesion)

        return redirect("pantalla_espera")

    return render(request, "fase4/peer_review.html", {
        "session": sesion,
        "evaluator_team": grupo_evaluador,
        "grupo_objetivo": grupo_objetivo,
        "mi_equipo_presenta": False,
        "ya_evaluo": ya_evaluo,
        "criteria": criteria,
    })

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