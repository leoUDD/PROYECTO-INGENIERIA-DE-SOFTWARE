from django.db.models import F
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from juego.backend.fase5.services import peer_review_completado
from juego.models import Grupo, Evaluacion

from juego.backend.core_global.services import (
    acceso_permitido,
    obtener_grupo_desde_session,
    avanzar_al_siguiente_pitch_o_ranking,
    borrar_fotos_lego_sesion,
)

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

        return render(request, "fase5/peer_review.html", {
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

    return render(request, "fase5/peer_review.html", {
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
    grupo_premiado.save(update_fields=["tokensgrupo"])

    grupo_evaluador.recompensa_peer_otorgada = True
    grupo_evaluador.save(update_fields=["recompensa_peer_otorgada"])


def evaluacion_actual_completa(sesion):
    grupo_actual = sesion.grupo_presentando

    if not grupo_actual:
        return False

    total_evaluadores = (
        Grupo.objects
        .filter(sesion=sesion)
        .exclude(pk=grupo_actual.pk)
        .count()
    )

    realizadas = (
        Evaluacion.objects
        .filter(
            sesion=sesion,
            grupo_evaluado=grupo_actual,
        )
        .exclude(grupo_evaluador=grupo_actual)
        .count()
    )

    return total_evaluadores > 0 and realizadas >= total_evaluadores

def reflexion(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")

    if grupo and grupo.sesion:
        borrar_fotos_lego_sesion(grupo.sesion)    

    if not acceso_permitido(grupo, "reflexion"):
        return redirect("pantalla_espera")

    return render(request, "fase5/reflexion.html", {"grupo": grupo})

def finalizar_mision(request):
    request.session.pop("grupo_id", None)
    return redirect("perfiles")

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