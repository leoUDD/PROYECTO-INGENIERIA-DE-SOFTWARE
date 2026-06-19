from django.shortcuts import render, redirect

from juego.backend.core_global.services import obtener_grupo_desde_session, acceso_permitido


def pantalla_inicio(request):
    grupo = obtener_grupo_desde_session(request)

    if not grupo:
        return redirect("registro")

    if not acceso_permitido(grupo, "pantalla_inicio"):
        return redirect("pantalla_espera")

    return render(request, "pantalla_inicio.html", {"grupo": grupo})