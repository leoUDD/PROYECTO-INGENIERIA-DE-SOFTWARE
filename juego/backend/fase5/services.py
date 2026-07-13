from django.db.models import F

from juego.backend.core_global.services import (
    avanzar_al_siguiente_pitch_o_ranking,
)
from juego.models import Evaluacion, Grupo


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

    evaluaciones = (
        Evaluacion.objects
        .filter(
            sesion=sesion,
            grupo_evaluador=grupo_evaluador,
        )
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

    mejor_evaluacion = evaluaciones.first()

    if not mejor_evaluacion:
        return

    grupo_premiado = mejor_evaluacion.grupo_evaluado
    grupo_premiado.tokensgrupo = (
        grupo_premiado.tokensgrupo or 0
    ) + 2
    grupo_premiado.save(update_fields=["tokensgrupo"])

    grupo_evaluador.recompensa_peer_otorgada = True
    grupo_evaluador.save(
        update_fields=["recompensa_peer_otorgada"]
    )


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

    return (
        total_evaluadores > 0
        and realizadas >= total_evaluadores
    )