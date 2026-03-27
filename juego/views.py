#NUEVO
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
#NUEVO CIERRRE
from django.shortcuts import redirect, render
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .tematicas_data import get_theme
import openpyxl
import pandas as pd
from .models import Alumno, Profesor, Usuario, Grupo, Desafio, Idadministrador, Sesion, Reto, Retogrupo, Evaluacion
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
    "pantalla_espera",

    # Fase 1
    "pantalla_inicio",
    "promptconocidos",
    "introducciones",
    "conocidos",
    "trabajoenequipo",
    "minijuego1",
    "transiciondesafio",

    # Fase 2
    "transicionempatia",
    "tematicas",
    "desafios",
    "bubblemap",
    "transicioncreatividad",

    # Fase 3
    "lego",
    "transicioncomunicacion",

    # Fase 4
    "pitch",
    "presentar_pitch",
    "orden_presentacion_alumno",
    "transicionapoyo",
]

RUTA_POR_FASE = {
    "pantalla_espera": "pantalla_espera",
    "pantalla_inicio": "pantalla_inicio",
    "promptconocidos": "promptconocidos",
    "introducciones": "introducciones",
    "conocidos": "conocidos",
    "trabajoenequipo": "trabajoenequipo",
    "minijuego1": "minijuego1",
    "transiciondesafio": "transiciondesafio",
    "transicionempatia": "transicionempatia",
    "tematicas": "tematicas",
    "desafios": "desafios",
    "bubblemap": "bubblemap",
    "transicioncreatividad": "transicioncreatividad",
    "lego": "lego",
    "transicioncomunicacion": "transicioncomunicacion",
    "pitch": "pitch",
    "presentar_pitch": "presentar_pitch",
    "orden_presentacion_alumno": "orden_presentacion_alumno",
    "transicionapoyo": "transicionapoyo",
}

ETIQUETA_FASE = {
    "pantalla_espera": "Lobby / Espera",
    "pantalla_inicio": "F1 · Inicio",
    "promptconocidos": "F1 · ¿Se conocen?",
    "introducciones": "F1 · Introducciones",
    "conocidos": "F1 · Ya se conocen",
    "trabajoenequipo": "F1 · Trabajo en equipo",
    "minijuego1": "F1 · Minijuego",
    "transiciondesafio": "F1 → F2 · Transición",
    "transicionempatia": "F2 · Introducción",
    "tematicas": "F2 · Temáticas",
    "desafios": "F2 · Desafíos",
    "bubblemap": "F2 · Bubble Map",
    "transicioncreatividad": "F2 → F3 · Transición",
    "lego": "F3 · LEGO",
    "transicioncomunicacion": "F3 → F4 · Transición",
    "pitch": "F4 · Pitch",
    "presentar_pitch": "F4 · Presentar pitch",
    "orden_presentacion_alumno": "F4 · Orden de presentación",
    "transicionapoyo": "Cierre / Apoyo",
}

def obtener_grupo_desde_session(request):
    grupo_id = request.session.get("grupo_id")
    if not grupo_id:
        return None
    try:
        return Grupo.objects.select_related("sesion").get(pk=grupo_id)
    except Grupo.DoesNotExist:
        return None

def acceso_permitido(grupo, nombre_vista):
    if not grupo or not grupo.sesion:
        return False
    return grupo.sesion.fase_actual == nombre_vista


@require_GET
def estado_sesion(request, sesion_id):
    sesion = get_object_or_404(Sesion, pk=sesion_id)
    grupos = Grupo.objects.filter(sesion=sesion).order_by("idgrupo")

    fase_actual = sesion.fase_actual
    nombre_url = RUTA_POR_FASE.get(fase_actual, "pantalla_espera")

    data = {
        "sesionId": sesion.idsesion,
        "faseActual": fase_actual,
        "faseEtiqueta": ETIQUETA_FASE.get(fase_actual, fase_actual),
        "rutaAlumno": reverse(nombre_url),
        "timerCorriendo": sesion.timer_corriendo,
        "segundosRestantes": sesion.segundos_restantes,
        "grupos": [
            {
                "id": g.idgrupo,
                "nombre": g.nombregrupo,
                "tokens": g.tokensgrupo or 0,
                "listoLobby": g.listo_lobby,
                "listoF1": g.listo_f1,
                "listoF2": g.listo_f2,
                "listoF3": g.listo_f3,
                "listoF4": g.listo_f4,
            }
            for g in grupos
        ]
    }
    return JsonResponse(data)


@require_POST
def profesor_actualizar_estado(request, sesion_id):
    sesion = get_object_or_404(Sesion, pk=sesion_id)
    payload = json.loads(request.body or "{}")

    if "faseActual" in payload:
        nueva = payload["faseActual"]
        if nueva not in FASES_ORDEN:
            return JsonResponse({"ok": False, "error": "Pantalla inválida"}, status=400)
        sesion.fase_actual = nueva

    if "timerCorriendo" in payload:
        sesion.timer_corriendo = bool(payload["timerCorriendo"])

    if "segundosRestantes" in payload:
        sesion.segundos_restantes = int(payload["segundosRestantes"])

    # tiempos automáticos solo para pantallas/juegos principales
    tiempos = {
        "trabajoenequipo": sesion.t_rompehielo,
        "tematicas": sesion.t_empatia,
        "lego": sesion.t_creatividad,
        "pitch": sesion.t_pitch,
    }

    if payload.get("faseActual") in tiempos:
        sesion.segundos_restantes = tiempos[payload["faseActual"]]
        sesion.timer_corriendo = False

    sesion.save()

    return JsonResponse({
        "ok": True,
        "faseActual": sesion.fase_actual,
        "faseEtiqueta": ETIQUETA_FASE.get(sesion.fase_actual, sesion.fase_actual),
        "rutaAlumno": reverse(RUTA_POR_FASE.get(sesion.fase_actual, "pantalla_espera")),
        "timerCorriendo": sesion.timer_corriendo,
        "segundosRestantes": sesion.segundos_restantes,
    })


@require_POST
def profesor_siguiente_fase(request, sesion_id):
    sesion = get_object_or_404(Sesion, pk=sesion_id)

    try:
        idx = FASES_ORDEN.index(sesion.fase_actual)
    except ValueError:
        return JsonResponse({"ok": False, "error": "Pantalla actual inválida"}, status=400)

    if idx + 1 >= len(FASES_ORDEN):
        return JsonResponse({"ok": False, "error": "Ya está en la última pantalla"}, status=400)

    sesion.fase_actual = FASES_ORDEN[idx + 1]

    tiempos = {
        "trabajoenequipo": sesion.t_rompehielo,
        "tematicas": sesion.t_empatia,
        "lego": sesion.t_creatividad,
        "pitch": sesion.t_pitch,
    }

    if sesion.fase_actual in tiempos:
        sesion.segundos_restantes = tiempos[sesion.fase_actual]
        sesion.timer_corriendo = False

    sesion.save()

    return JsonResponse({
        "ok": True,
        "faseActual": sesion.fase_actual,
        "faseEtiqueta": ETIQUETA_FASE.get(sesion.fase_actual, sesion.fase_actual),
        "rutaAlumno": reverse(RUTA_POR_FASE.get(sesion.fase_actual, "pantalla_espera")),
        "segundosRestantes": sesion.segundos_restantes,
    })

@require_GET
def estado_sesion(request, sesion_id):
    sesion = get_object_or_404(Sesion, pk=sesion_id)
    grupos = Grupo.objects.filter(sesion=sesion).order_by("idgrupo")

    data = {
        "sesionId": sesion.idsesion,
        "faseActual": sesion.fase_actual,
        "timerCorriendo": sesion.timer_corriendo,
        "segundosRestantes": sesion.segundos_restantes,
        "grupos": [
            {
                "id": g.idgrupo,
                "nombre": g.nombregrupo,
                "tokens": g.tokensgrupo or 0,
                "listoLobby": g.listo_lobby,
                "listoF1": g.listo_f1,
                "listoF2": g.listo_f2,
                "listoF3": g.listo_f3,
                "listoF4": g.listo_f4,
            }
            for g in grupos
        ]
    }
    return JsonResponse(data)


@require_POST
def marcar_grupo_listo(request, grupo_id):
    grupo = get_object_or_404(Grupo, pk=grupo_id)
    payload = json.loads(request.body or "{}")
    fase = payload.get("fase")

    if fase == "lobby":
        grupo.listo_lobby = True
    elif fase == "f1":
        grupo.listo_f1 = True
    elif fase == "f2":
        grupo.listo_f2 = True
    elif fase == "f3":
        grupo.listo_f3 = True
    elif fase == "f4":
        grupo.listo_f4 = True
    else:
        return JsonResponse({"ok": False, "error": "Fase inválida"}, status=400)

    grupo.save()
    return JsonResponse({"ok": True})


@require_POST
def profesor_actualizar_estado(request, sesion_id):
    sesion = get_object_or_404(Sesion, pk=sesion_id)
    payload = json.loads(request.body or "{}")

    if "faseActual" in payload:
        sesion.fase_actual = payload["faseActual"]

    if "timerCorriendo" in payload:
        sesion.timer_corriendo = bool(payload["timerCorriendo"])

    if "segundosRestantes" in payload:
        sesion.segundos_restantes = int(payload["segundosRestantes"])

    sesion.save()

    return JsonResponse({
        "ok": True,
        "faseActual": sesion.fase_actual,
        "timerCorriendo": sesion.timer_corriendo,
        "segundosRestantes": sesion.segundos_restantes,
    })


@require_POST
def profesor_siguiente_fase(request, sesion_id):
    sesion = get_object_or_404(Sesion, pk=sesion_id)

    try:
        idx = FASES_ORDEN.index(sesion.fase_actual)
    except ValueError:
        return JsonResponse({"ok": False, "error": "Fase actual inválida"}, status=400)

    if idx + 1 >= len(FASES_ORDEN):
        return JsonResponse({"ok": False, "error": "Ya está en la última fase"}, status=400)

    sesion.fase_actual = FASES_ORDEN[idx + 1]

    # opcional: cargar tiempo automáticamente
    tiempos = {
        "f1_juego": sesion.t_rompehielo,
        "f2_juego": sesion.t_empatia,
        "f3_juego": sesion.t_creatividad,
        "f4_juego": sesion.t_pitch,
    }

    if sesion.fase_actual in tiempos:
        sesion.segundos_restantes = tiempos[sesion.fase_actual]
        sesion.timer_corriendo = False

    sesion.save()

    return JsonResponse({
        "ok": True,
        "faseActual": sesion.fase_actual,
        "segundosRestantes": sesion.segundos_restantes,
    })


def pantalla_espera(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        messages.error(request, "Debes ingresar con tu código.")
        return redirect("registro")

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

def tematicas(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")
    if not acceso_permitido(grupo, "tematicas"):
        return redirect("pantalla_espera")
    return render(request, "tematicas.html", {"grupo": grupo})

def lego(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")
    if not acceso_permitido(grupo, "lego"):
        return redirect("pantalla_espera")
    return render(request, "lego.html", {"grupo": grupo})


#NUEVO CIERRRE
def perfiles(request):
    return render(request, 'perfiles.html')


def bienvenida(request):
    return render(request, 'bienvenida.html')


def registro(request):
    error = None

    if request.method == 'POST':
        codigo = request.POST.get('id_grupo', '').strip()

        if not codigo:
            error = "Debes ingresar un código."
            return render(request, 'registro.html', {'error': error})

        try:
            grupo = Grupo.objects.get(codigoacceso=codigo)
        except Grupo.DoesNotExist:
            error = 'Código de grupo inválido'
            return render(request, 'registro.html', {'error': error})

        request.session['grupo_id'] = grupo.idgrupo

        return redirect('pantalla_espera')  # <-- ajusta al name de tu URL real

    return render(request, 'registro.html', {'error': error})





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
    return render(request, "minijuego1.html", {"grupo": grupo})

def sopa_completada(request):
    grupo_id = request.session.get("grupo_id")

    if not grupo_id:
        messages.error(request, "No se pudo identificar tu grupo.")
        return redirect("registro")

    grupo = get_object_or_404(Grupo, pk=grupo_id)

    if not grupo.sopa_ganada:
        grupo.tokensgrupo = (grupo.tokensgrupo or 0) + 3
        grupo.sopa_ganada = True
        grupo.save()

    return redirect("transiciondesafio")


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

def desafios(request):
    slug = (request.GET.get('tema') or request.session.get('tema') or '').lower()
    theme = get_theme(slug)
    if not theme:
        return redirect('tematicas')
    request.session['tema'] = slug
    return render(request, 'desafios.html', {'theme': theme, 'slug': slug})


def bubblemap(request):
    return render(request, 'bubblemap.html')

def orden_presentacion_alumno(request):
    grupo_id = request.session.get("grupo_id")
    if not grupo_id:
        messages.error(request, "No se pudo identificar tu grupo.")
        return redirect("registro")

    grupo_actual = get_object_or_404(Grupo, pk=grupo_id)
    sesion = grupo_actual.sesion

    grupos = Grupo.objects.filter(sesion=sesion).order_by('idgrupo')

    orden_existente = any(g.orden_presentacion for g in grupos)

    if request.method == "POST":
        if orden_existente:
            messages.warning(request, "El orden ya fue sorteado y no puede modificarse.")
            return redirect("orden_presentacion_alumno")

        lista = list(grupos)
        random.shuffle(lista)

        for pos, g in enumerate(lista, start=1):
            g.orden_presentacion = pos
            g.save()

        messages.success(request, "Orden sorteado correctamente.")
        return redirect("orden_presentacion_alumno")

    context = {
        "grupos": grupos.order_by('orden_presentacion'),
        "grupo_actual": grupo_actual,
        "orden_existente": orden_existente,
    }

    return render(request, "orden_presentacion_alumno.html", context)

def pitch(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")
    if not acceso_permitido(grupo, "pitch"):
        return redirect("pantalla_espera")
    return render(request, "pitch.html", {"grupo": grupo})


def presentar_pitch(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")

    return render(request, "presentar_pitch.html", {"grupo": grupo})


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

def peer_review_view(request):
    grupo_id = request.session.get("grupo_id")
    if not grupo_id:
        messages.error(request, "No pudimos identificar tu grupo.")
        return redirect("registro")

    grupo_evaluador = get_object_or_404(Grupo, pk=grupo_id)
    sesion = grupo_evaluador.sesion

    if not sesion:
        messages.error(request, "Tu grupo no está asociado a ninguna sesión.")
        return redirect("registro")

    all_targets = (
        Grupo.objects
        .filter(sesion=sesion)
        .exclude(pk=grupo_evaluador.pk)
    )

    evaluaciones_hechas = Evaluacion.objects.filter(
        sesion=sesion,
        grupo_evaluador=grupo_evaluador,
    )
    evaluados_ids = set(
        evaluaciones_hechas.values_list("grupo_evaluado_id", flat=True)
    )

    pending_targets = all_targets.exclude(pk__in=evaluados_ids)
    completed = not pending_targets.exists()  # True si ya evaluó a todos

    if completed and not getattr(grupo_evaluador, "recompensa_peer_otorgada", False):
        otorgar_tokens_peer_review(grupo_evaluador)

    criteria = [
        {"key": "claridad",     "label": "Claridad de la solución"},
        {"key": "creatividad",  "label": "Creatividad / innovación"},
        {"key": "viabilidad",   "label": "Viabilidad del proyecto"},
        {"key": "equipo",       "label": "Trabajo en equipo"},
        {"key": "presentacion", "label": "Calidad de la presentación / pitch"},
    ]

    if request.method == "POST" and not completed:
        target_team_id = request.POST.get("target_team_id")
        comment = request.POST.get("comment", "").strip()
        reflection = request.POST.get("reflection", "").strip()
        confirm = request.POST.get("confirm_honesty")

        try:
            grupo_evaluado = pending_targets.get(pk=target_team_id)
        except (Grupo.DoesNotExist, ValueError, TypeError):
            messages.error(
                request,
                "Debes seleccionar un equipo válido que aún no hayas evaluado."
            )
            return redirect("peer_review")

        if not comment:
            messages.error(request, "El comentario es obligatorio.")
            return redirect("peer_review")

        if not confirm:
            messages.error(request, "Debes confirmar que la evaluación es honesta.")
            return redirect("peer_review")

        scores = {}
        for c in criteria:
            val = request.POST.get(f"score_{c['key']}")
            if val not in ["1", "2", "3", "4", "5"]:
                messages.error(request, "Debes completar todos los criterios.")
                return redirect("peer_review")
            scores[c["key"]] = int(val)

        if Evaluacion.objects.filter(
            sesion=sesion,
            grupo_evaluador=grupo_evaluador,
            grupo_evaluado=grupo_evaluado
        ).exists():
            messages.info(request, "Ya habías evaluado a ese equipo.")
            return redirect("peer_review")

        Evaluacion.objects.create(
            sesion=sesion,
            grupo_evaluador=grupo_evaluador,
            grupo_evaluado=grupo_evaluado,
            claridad=scores["claridad"],
            creatividad=scores["creatividad"],
            viabilidad=scores["viabilidad"],
            equipo=scores["equipo"],
            presentacion=scores["presentacion"],
            comentario=comment,
            reflexion=reflection or None,
        )

        messages.success(request, "¡Evaluación enviada para ese equipo!")
        return redirect("peer_review")

    context = {
        "session": sesion,
        "evaluator_team": grupo_evaluador,
        "target_teams": pending_targets,
        "criteria": criteria,
        "submitted": completed,
        "evaluados_count": len(evaluados_ids),
        "total_targets": all_targets.count(),
    }
    return render(request, "peer_review.html", context)

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

def reflexion(request):
    return render(request, 'reflexion.html')

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
            fase_actual="pantalla_espera",
            timer_corriendo=False,
            segundos_restantes=0
        )

        messages.success(request, "Sesión creada correctamente.")
        return redirect('listar_sesiones')

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

        if current_rank == 1:
            medal = "🏆"
            podium_class = "podium-1"
        elif current_rank == 2:
            medal = "🥈"
            podium_class = "podium-2"
        elif current_rank == 3:
            medal = "🥉"
            podium_class = "podium-3"
        else:
            medal = ""
            podium_class = ""

        rankings.append({
            "team_name": g.nombregrupo or f"Grupo {g.idgrupo}",
            "tokens": tokens,
            "is_me": g.idgrupo == grupo_actual.idgrupo,
            "rank": current_rank,
            "medal": medal,
            "podium_class": podium_class,
        })

    context = {
        "session": sesion,
        "rankings": rankings,
    }
    return render(request, "ranking.html", context)

def mision_cumplida_view(request):
    """
    Pantalla final de cierre de misión antes del ranking.
    """
    return render(request, "mision_cumplida.html")

def preview_pantalla_profesor(request, sesion_id):
    sesion = get_object_or_404(Sesion, pk=sesion_id)

    plantilla_por_fase = {
        "pantalla_espera": "pantalla_espera_preview.html",
        "pantalla_inicio": "pantalla_inicio.html",
        "promptconocidos": "promptconocidos.html",
        "introducciones": "introducciones.html",
        "conocidos": "conocidos.html",
        "trabajoenequipo": "trabajoenequipo.html",
        "minijuego1": "minijuego1.html",
        "transiciondesafio": "transiciondesafio.html",
        "transicionempatia": "transicionempatia.html",
        "tematicas": "tematicas.html",
        "desafios": "desafios.html",
        "bubblemap": "bubblemap.html",
        "transicioncreatividad": "transicioncreatividad.html",
        "lego": "lego.html",
        "transicioncomunicacion": "transicioncomunicacion.html",
        "pitch": "pitch.html",
        "presentar_pitch": "presentar_pitch.html",
        "orden_presentacion_alumno": "orden_presentacion_alumno.html",
        "transicionapoyo": "transicionapoyo.html",
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