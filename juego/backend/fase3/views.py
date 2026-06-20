import json

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from juego.models import Grupo, Sesion, BubbleMapRespuesta, RuletaLegoOpcion
from juego.backend.core_global.services import (
    acceso_permitido,
    obtener_grupo_desde_session,
    )



def transicioncreatividad(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")
    if not acceso_permitido(grupo, "transicioncreatividad"):
        return redirect("pantalla_espera")
    return render(request, "fase3/transicioncreatividad.html", {"grupo": grupo})

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

            limpiar_fotos_lego_por_desafio(grupo.desafio_elegido)

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
                "opciones_ruleta": RuletaLegoOpcion.objects.filter(activa=True).order_by("orden")[:8],
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

    return render(request, "fase3/lego.html", {
        "grupo": grupo,
        "desafio_nombre_actual": grupo.desafio_nombre or "Desafío no seleccionado",
        "desafio_descripcion_actual": grupo.desafio_descripcion or "Aún no hay descripción disponible para este desafío.",
        "tiempo_inicial_lego": grupo.sesion.segundos_restantes or 15,
        "opciones_ruleta": RuletaLegoOpcion.objects.filter(activa=True).order_by("orden")[:8],
    })

@require_POST
def aplicar_resultado_ruleta_lego(request):
    grupo = obtener_grupo_desde_session(request)

    if not grupo:
        return JsonResponse({"ok": False, "error": "Grupo no encontrado."}, status=403)

    try:
        payload = json.loads(request.body or "{}")
    except Exception:
        return JsonResponse({"ok": False, "error": "Solicitud inválida."}, status=400)

    delta = int(payload.get("tokens") or 0)

    if delta not in [-2, -1, 0, 1, 2]:
        return JsonResponse({"ok": False, "error": "Resultado inválido."}, status=400)

    with transaction.atomic():
        grupo = Grupo.objects.select_for_update().get(pk=grupo.pk)
        grupo.tokensgrupo = max((grupo.tokensgrupo or 0) + delta, 0)
        grupo.save(update_fields=["tokensgrupo"])

    return JsonResponse({
        "ok": True,
        "tokens": grupo.tokensgrupo,
        "delta": delta,
    })

def limpiar_fotos_lego_por_desafio(desafio):
    if not desafio:
        return

    grupos_con_foto = (
        Grupo.objects
        .filter(desafio_elegido=desafio)
        .exclude(foto_lego="")
        .exclude(foto_lego__isnull=True)
        .order_by("-idgrupo")
    )

    fotos_a_borrar = grupos_con_foto[7:]

    for grupo in fotos_a_borrar:
        if grupo.foto_lego:
            ruta = grupo.foto_lego.path

            if os.path.exists(ruta):
                os.remove(ruta)

            grupo.foto_lego = None
            grupo.save(update_fields=["foto_lego"])

def borrar_foto_lego_grupo(grupo):

    if grupo.foto_lego:
        try:
            grupo.foto_lego.delete(save=False)
        except Exception:
            pass

        grupo.foto_lego = None
        grupo.save(update_fields=["foto_lego"])