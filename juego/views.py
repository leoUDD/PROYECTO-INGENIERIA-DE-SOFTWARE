from django.shortcuts import redirect, render
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .tematicas_data import get_theme
import openpyxl
from . import models

# ===========================
# 📋 Vistas principales
# ===========================

def perfiles(request):
    return render(request, 'perfiles.html')


def registrarse(request):
    if request.method == 'POST':
        # Lógica de registro (ejemplo)
        user_name = request.POST.get('user_name')
        email = request.POST.get('email')
        carrera = request.POST.get('carrera')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Validación de contraseñas
        if password != confirm_password:
            error = 'Las contraseñas no coinciden'
            return render(request, 'registrarse.html', {'error': error})

        return redirect('login')
    return render(request, 'registrarse.html')


def login(request):
    if request.method == 'POST':
        # Lógica de autenticación (demo)
        email = request.POST.get('email')
        password = request.POST.get('password')
        if email == 'leo@udd.cl' and password == '1234':
            return render(request, 'bienvenida.html', {'email': email})
        if email == 'seba@udd.cl' and password == '1234':
            return render(request, 'bienvenida.html', {'email': email})
        if email == 'jesus@udd.cl' and password == '1234':
            return render(request, 'bienvenida.html', {'email': email})
        else:
            error = 'Credenciales inválidas'
            return render(request, 'login.html', {'error': error})

    return render(request, 'login.html')


def bienvenida(request):
    return render(request, 'bienvenida.html')


def registro(request):
    if request.method == 'POST':
        # Lógica para manejar el registro (ejemplo)
        id_grupo = request.POST.get('id_grupo')
        if id_grupo == '1234':
            return render(request, 'pantalla_inicio.html', {'id_grupo': id_grupo})
        else:
            error = 'ID de grupo inválido'
            return render(request, 'registro.html', {'error': error})
    return render(request, 'registro.html')

def trabajoenequipo(request):
    return render(request, 'trabajoenequipo.html')

def lego(request):
    return render(request, 'lego.html')


def crearequipo(request):
    return render(request, 'crearequipo.html')


def introducciones(request):
    return render(request, 'introducciones.html')

def pantalla_inicio(request):
    return render(request, 'pantalla_inicio.html')

def promptconocidos(request):
    return render(request, 'promptconocidos.html')


def conocidos(request):
    return render(request, 'conocidos.html')

def minijuego1(request):
    return render(request, 'minijuego1.html')

def intro_desafios(request):
    return render(request, 'intro_desafios.html')

def tematicas(request):
    return render(request, 'tematicas.html')

def dashboardprofesor(request):
    return render(request, 'dashboardprofesor.html')

def dashboardadmin(request):
    return render(request, 'dashboardadmin.html')

def registrarprofesor(request):
    return render(request, 'registrarprofesor.html')

def agregardesafio(request):
    return render(request, 'agregardesafio.html')

def transicionempatia(request):
    return render(request, 'transicionempatia.html')

def transicioncreatividad(request):
    return render(request, 'transicioncreatividad.html')

def transicioncomunicacion(request):
    return render(request, 'transicioncomunicacion.html')

def transiciondesafio(request):
    return render(request, 'transiciondesafio.html')

def cargar_alumnos(request):
    if request.method == "POST" and request.FILES.get("archivo_excel"):
        archivo = request.FILES["archivo_excel"]

        try:
            wb = openpyxl.load_workbook(archivo)
            hoja = wb.active
        except Exception:
            messages.error(request, "Error al leer el archivo Excel. Asegúrate de que sea un .xlsx válido.")
            return redirect("cargar_alumnos")

        profesor = models.Profesor.objects.first()  # ⚠️ Ajustar cuando haya login
        count = 0

        # Iterar sobre las filas del Excel, saltando el encabezado
        for fila in hoja.iter_rows(min_row=2, values_only=True):
            try:
                correo, rut, nombre, apellido_paterno, apellido_materno = fila[:5]
            except ValueError:
                continue  # si la fila está incompleta, la salta

            if not correo or not nombre:
                continue

            nombre_completo = f"{nombre} {apellido_paterno or ''} {apellido_materno or ''}".strip()

            # Evita duplicados por correo
            if not models.Alumno.objects.filter(emailalumno=correo).exists():
                models.Alumno.objects.create(
                    profesor_idprofesor=profesor,
                    emailalumno=correo,
                    nombrealumno=nombre_completo,
                    carreraalumno="No especificada",  # temporal
                )
                count += 1

        messages.success(request, f"✅ Se cargaron {count} alumnos correctamente.")
        return redirect("dashboardprofesor")

    return render(request, "registro/cargar_alumnos.html")

def agregar_alumno_manual(request):
    if request.method == "POST":
        correo = request.POST.get("email", "").strip()
        nombre = request.POST.get("nombre", "").strip()
        ap_paterno = request.POST.get("apellido_paterno", "").strip()
        ap_materno = request.POST.get("apellido_materno", "").strip()
        carrera = request.POST.get("carrera", "").strip()

        if not correo or not nombre:
            messages.warning(request, "Correo y Nombre son obligatorios.")
            return redirect("dashboardprofesor")

        profesor = models.Profesor.objects.first()  # TODO: usar el profesor autenticado

        if models.Alumno.objects.filter(emailalumno=correo).exists():
            messages.warning(request, "⚠️ Ya existe un alumno con ese correo.")
            return redirect("dashboardprofesor")

        models.Alumno.objects.create(
            profesor_idprofesor=profesor,
            emailalumno=correo,
            nombrealumno=f"{nombre} {ap_paterno} {ap_materno}".strip(),
            carreraalumno=carrera or "No especificada",
        )
        messages.success(request, "✅ Alumno agregado correctamente.")
        return redirect("dashboardprofesor")

    return redirect("dashboardprofesor")

def desafios(request):
    slug = (request.GET.get('tema') or request.session.get('tema') or '').lower()
    theme = get_theme(slug)
    if not theme:
        return redirect('tematicas')
    request.session['tema'] = slug
    return render(request, 'desafios.html', {'theme': theme, 'slug': slug})

def bubblemap(request):
    return render(request, 'bubblemap.html')

def pitch(request):
    return render(request, 'pitch.html')

def registraralumnos(request):
    return render(request, 'registraralumnos.html') 
# ===========================
# 🛒 MERCADO DE RETOS
# ===========================

def market_view(request):
    # Saldo temporal (luego se conectará con la BD)
    user_tokens = 12

    # Catálogo de retos disponibles
    challenges = [
        {"id": 1, "title": "Problema matemático", "description": "Dos integrantes resuelven un problema en 3 minutos.", "cost": 5},
        {"id": 2, "title": "LEGO exprés", "description": "Prototipo con LEGO en 5 minutos.", "cost": 8},
        {"id": 3, "title": "Pitch relámpago", "description": "Presentación de 60 segundos con idea clave.", "cost": 6},
    ]

    # Equipos a los que se puede retar (de ejemplo)
    other_teams = [
        {"id": 2, "name": "Equipo Beta"},
        {"id": 3, "name": "Equipo Gamma"},
    ]

    context = {
        "user_tokens": user_tokens,
        "challenges": challenges,
        "other_teams": other_teams,
    }

    return render(request, "market.html", context)


@require_http_methods(["POST"])
def issue_challenge_view(request, challenge_id):
    target_team_id = request.POST.get("target_team_id")

    # Catálogo temporal
    challenge_catalog = {
        1: {"title": "Problema matemático", "cost": 5},
        2: {"title": "LEGO exprés", "cost": 8},
        3: {"title": "Pitch relámpago", "cost": 6},
    }

    challenge = challenge_catalog.get(int(challenge_id))
    if not challenge:
        messages.error(request, "Reto no encontrado.")
        return redirect("market")

    # Simular validación de saldo
    user_tokens = 12  # se reemplazará por el saldo real en BD
    if not target_team_id:
        messages.error(request, "Selecciona un equipo objetivo.")
        return redirect("market")
    if user_tokens < challenge["cost"]:
        messages.error(request, "No tienes tokens suficientes.")
        return redirect("market")

    # Mensaje de éxito
    messages.success(
        request,
        f"Has retado al equipo {target_team_id} con “{challenge['title']}” por {challenge['cost']} tokens."
    )
    return redirect("market")


# ===========================
# 🧩 EVALUACIÓN (Peer Review)
# ===========================

def peer_review_view(request, session_id):
    # Datos MOCK para que funcione sin BD (luego lo conectan a sus modelos)
    class Obj:
        pass

    session = Obj()
    session.name = "Sesión Demo"

    evaluator_team = Obj()
    evaluator_team.id = 1
    evaluator_team.name = "Equipo Alpha"

    target_teams = []
    for i, name in [(2, "Equipo Beta"), (3, "Equipo Gamma"), (4, "Equipo Delta")]:
        t = Obj()
        t.id = i
        t.name = name
        target_teams.append(t)

    criteria = [
        {"key": "claridad", "label": "Claridad de la solución"},
        {"key": "creatividad", "label": "Creatividad/Innovación"},
        {"key": "viabilidad", "label": "Viabilidad"},
        {"key": "equipo", "label": "Trabajo en equipo"},
        {"key": "presentacion", "label": "Presentación (TED)"},
    ]

    context = {
        "session": session,
        "evaluator_team": evaluator_team,
        "target_teams": target_teams,
        "criteria": criteria,
        "submitted": False,
    }

    if request.method == "POST":
        # Aquí podrías procesar y guardar; por ahora solo mostramos "enviado"
        context["submitted"] = True

    return render(request, "evaluation/peer_review.html", context)