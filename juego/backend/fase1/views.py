import json

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.db import transaction
from django.db.models import F
from django.urls import reverse
from django.utils import timezone

from juego.models import (
    Grupo,
    Sesion,
    PalabraSopaEncontrada,
)

from juego.backend.core_global.services import (
    obtener_grupo_desde_session,
    acceso_permitido,
)


def pantalla_inicio(request):
    grupo = obtener_grupo_desde_session(request)

    if not grupo:
        return redirect("registro")

    if not acceso_permitido(grupo, "pantalla_inicio"):
        return redirect("pantalla_espera")

    return render(request, "fase1/pantalla_inicio.html", {"grupo": grupo})


def promptconocidos(request):
    grupo = obtener_grupo_desde_session(request)

    if not grupo:
        return redirect("registro")

    if not acceso_permitido(grupo, "promptconocidos"):
        return redirect("pantalla_espera")

    return render(request, "fase1/promptconocidos.html", {"grupo": grupo})

def elegir_modo_conocidos(request, modo):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")

    if not acceso_permitido(grupo, "promptconocidos"):
        return redirect("pantalla_espera")

    request.session["modo_conocidos"] = modo
    request.session.modified = True

    if modo == "rapido":
        return redirect("conocidos_rapido")

    return redirect("conocidos")

def conocidos(request):
    grupo = obtener_grupo_desde_session(request)

    if not grupo:
        return redirect("registro")

    if not acceso_permitido(grupo, "conocidos"):
        return redirect("pantalla_espera")

    return render(request, "fase1/conocidos.html", {
        "grupo": grupo,
        "modo_rapido": False,
    })


def conocidos_rapido(request):
    grupo = obtener_grupo_desde_session(request)

    if not grupo:
        return redirect("registro")

    if not acceso_permitido(grupo, "conocidos_rapido"):
        return redirect("pantalla_espera")

    return render(request, "fase1/conocidos.html", {
        "grupo": grupo,
        "modo_rapido": True,
    })

def trabajoenequipo(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")
    if not acceso_permitido(grupo, "trabajoenequipo"):
        return redirect("pantalla_espera")
    return render(request, "fase1/trabajoenequipo.html", {"grupo": grupo})

def minijuego1(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")
    if not acceso_permitido(grupo, "minijuego1"):
        return redirect("pantalla_espera")
    return render(request, "fase1/minijuego1.html", {
        "grupo": grupo,
        "sopa_ganada": bool(grupo.sopa_ganada),
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

@require_POST
def sopa_completada(request):
    grupo = obtener_grupo_desde_session(request)

    if not grupo:
        return JsonResponse({
            "ok": False,
            "error": "No se pudo identificar tu grupo."
        }, status=403)

    with transaction.atomic():
        grupo = Grupo.objects.select_for_update().get(pk=grupo.pk)
        sesion = Sesion.objects.select_for_update().get(pk=grupo.sesion_id)

        if grupo.sopa_ganada:
            return JsonResponse({
                "ok": True,
                "ya_completada": True,
                "bonus_otorgado": 0,
                "primer_equipo": False,
                "todos_terminaron": False,
                "ranking_disparado": False,
                "faseActual": sesion.fase_actual,
                "rutaAlumno": reverse("minijuego1"),
                "sopa_tiempo_segundos": grupo.sopa_tiempo_segundos,
            })

        ya_habia_otro = Grupo.objects.select_for_update().filter(
            sesion=sesion,
            sopa_ganada=True
        ).exclude(pk=grupo.pk).exists()

        primer_equipo = not ya_habia_otro

        # Regla:
        # - Primer equipo: 5 tokens
        # - Equipos siguientes: 3 tokens
        bonus = 5 if primer_equipo else 3

        ahora = timezone.now()

        # Tiempo usado desde que comenzó realmente el timer de la fase.
        # Si por alguna razón no existe timer_inicio_at, se guarda None.
        tiempo_segundos = None

        if sesion.timer_inicio_at:
            tiempo_segundos = int((ahora - sesion.timer_inicio_at).total_seconds())
            tiempo_segundos = max(tiempo_segundos, 0)

        grupo.tokensgrupo = (grupo.tokensgrupo or 0) + bonus
        grupo.sopa_ganada = True
        grupo.sopa_tiempo_segundos = tiempo_segundos
        grupo.sopa_completada_en = ahora

        grupo.save(update_fields=[
            "tokensgrupo",
            "sopa_ganada",
            "sopa_tiempo_segundos",
            "sopa_completada_en",
        ])

        total_grupos = Grupo.objects.filter(sesion=sesion).count()
        grupos_terminados = Grupo.objects.filter(
            sesion=sesion,
            sopa_ganada=True
        ).count()

        todos_terminaron = total_grupos > 0 and grupos_terminados == total_grupos
        ranking_disparado = False

        if todos_terminaron:
            sesion.fase_actual = "f1_ranking"
            sesion.segundos_restantes = 0
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

            ranking_disparado = True

    return JsonResponse({
        "ok": True,
        "bonus_otorgado": bonus,
        "primer_equipo": primer_equipo,
        "todos_terminaron": todos_terminaron,
        "ranking_disparado": ranking_disparado,
        "gruposTerminados": grupos_terminados,
        "totalGrupos": total_grupos,
        "faseActual": sesion.fase_actual,
        "rutaAlumno": reverse("ranking") if ranking_disparado else reverse("minijuego1"),
        "sopa_tiempo_segundos": tiempo_segundos,
    })