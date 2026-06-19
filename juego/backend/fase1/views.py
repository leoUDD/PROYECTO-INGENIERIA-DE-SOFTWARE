from django.shortcuts import render, redirect

from juego.backend.core_global.services import obtener_grupo_desde_session, acceso_permitido


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
