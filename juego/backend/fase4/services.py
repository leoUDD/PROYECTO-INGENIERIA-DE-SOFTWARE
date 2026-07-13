from django.utils import timezone

from juego.models import Grupo


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
        segundos_restantes = max(
            int((sesion.timer_fin_at - timezone.now()).total_seconds()),
            0
        )

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

        "ordenSorteado": getattr(sesion, "orden_sorteado", False),
        "timerCorriendo": sesion.timer_corriendo,
        "segundosRestantes": segundos_restantes,
        "miPitch": grupo_solicitante.pitch_texto if grupo_solicitante else "",
        "miEquipoPresenta": (
            grupo_solicitante
            and grupo_actual
            and grupo_solicitante.idgrupo == grupo_actual.idgrupo
        ),
    }