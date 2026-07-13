import random

from django.contrib import messages
from django.shortcuts import redirect, render

from juego.models import Grupo

def perfiles(request):
    return render(request, 'perfiles.html')

def salir_grupo(request):
    request.session.flush()
    messages.success(request, "Sesión del grupo cerrada correctamente.")
    return redirect("registro")

def bienvenida(request):
    return render(request, 'bienvenida.html')

def registro(request):
    error = None

    nombres_aleatorios = [
        "Equipo Cóndor",
        "Misión Alfa",
        "Agentes UDD",
        "Mentes Creativas",
        "Los Innovadores",
        "Escuadrón Delta",
        "Visionarios UDD",
        "Código Naranja",
        "Equipo Fénix",
        "StartUp Squad",
        "Los Estrategas",
        "Comando Emprende",
    ]

    if request.method == "POST":
        codigo = (request.POST.get("id_grupo") or "").strip()
        nombre_grupo = (request.POST.get("nombre_grupo") or "").strip()

        if not codigo:
            error = "Debes ingresar el código de escuadrón"
            return render(request, "registro.html", {"error": error})

        try:
            grupo = Grupo.objects.select_related("sesion").get(codigoacceso__iexact=codigo)
        except Grupo.DoesNotExist:
            error = "Código de grupo inválido"
            return render(request, "registro.html", {"error": error})

        if not grupo.sesion:
            error = "Este grupo no está asociado a ninguna sesión"
            return render(request, "registro.html", {"error": error})

        if not nombre_grupo:
            nombre_grupo = random.choice(nombres_aleatorios)

        grupo.nombregrupo = nombre_grupo[:100]
        grupo.save(update_fields=["nombregrupo"])

        request.session.flush()
        request.session.cycle_key()
        request.session["grupo_id"] = grupo.idgrupo
        request.session["sesion_id"] = grupo.sesion_id
        request.session["ranking_flags_reseteados"] = False
        request.session.modified = True

        print(
            f"registro -> codigo={codigo} | grupo={grupo.idgrupo} "
            f"| nombre={grupo.nombregrupo} | sesion={grupo.sesion.idsesion if grupo.sesion else 'SIN SESION'}"
        )

        return redirect("bienvenida")

    return render(request, "registro.html", {"error": error})