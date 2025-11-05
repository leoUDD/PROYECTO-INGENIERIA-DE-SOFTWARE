from django.shortcuts import redirect, render
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .tematicas_data import get_theme
import openpyxl
from . import models
import pandas as pd
from .forms import UploadExcelForm
from .models import Alumno, Profesor, Usuario
from django.db import transaction
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import secrets
from django.shortcuts import get_object_or_404


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


def transicionapoyo(request):
    return render(request, 'transicionapoyo.html')


def cargar_alumnos(request):
    # Filtro por profesor, con fallback para no dejar vacío
    profesor = Profesor.objects.first()
    if profesor:
        alumnos = Alumno.objects.filter(profesor_idprofesor=profesor).order_by('idalumno')
    else:
        alumnos = Alumno.objects.all().order_by('idalumno')

    if request.method == "POST" and request.FILES.get("archivo_excel"):
        archivo = request.FILES["archivo_excel"]

        try:
            # Leer archivo, xlsx o csv
            if archivo.name.lower().endswith('.xlsx'):
                df = pd.read_excel(archivo)
            elif archivo.name.lower().endswith('.csv'):
                df = pd.read_csv(archivo)
            else:
                messages.error(request, "Formato no soportado. Usa .xlsx o .csv")
                return render(request, "registraralumnos.html", {"alumnos": alumnos})

            # Insertar alumnos
            with transaction.atomic():
                for _, row in df.iterrows():
                    Alumno.objects.create(
                        profesor_idprofesor=profesor,
                        emailalumno=row.get('Correo'),
                        rutalumno=row.get('RUT'),
                        nombrealumno=row.get('Nombre'),
                        apellidopaternoalumno=row.get('Apellido Paterno'),
                        apellidomaternoalumno=row.get('Apellido Materno'),
                        carreraalumno=''  # cambiar eventualmente
                    )

            messages.success(request, "Alumnos cargados correctamente.")

            # refrescar lista
            if profesor:
                alumnos = Alumno.objects.filter(profesor_idprofesor=profesor).order_by('idalumno')
            else:
                alumnos = Alumno.objects.all().order_by('idalumno')

        except Exception as e:
            messages.error(request, f"Error al leer el archivo: {e}")

    return render(request, "registraralumnos.html", {"alumnos": alumnos})


@require_http_methods(["POST"])
def agregar_alumno_manual(request):
    correo = (request.POST.get("email") or "").strip()
    nombre = (request.POST.get("nombre") or "").strip()
    ap_paterno = (request.POST.get("apellido_paterno") or "").strip()
    ap_materno = (request.POST.get("apellido_materno") or "").strip()
    carrera = (request.POST.get("carrera") or "").strip()

    if not correo or not nombre:
        messages.warning(request, "Correo y Nombre son obligatorios.")
        return redirect("registraralumnos")

    profesor = Profesor.objects.first()  # TODO: profesor autenticado

    if Alumno.objects.filter(emailalumno=correo).exists():
        messages.warning(request, "⚠️ Ya existe un alumno con ese correo.")
        return redirect("registraralumnos")

    try:
        with transaction.atomic():
            Alumno.objects.create(
                profesor_idprofesor=profesor,
                emailalumno=correo,
                nombrealumno=f"{nombre} {ap_paterno} {ap_materno}".strip(),
                carreraalumno=carrera or "No especificada",
            )
        messages.success(request, "✅ Alumno agregado correctamente.")
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


def pitch(request):
    return render(request, 'pitch.html')


def presentar_pitch(request):
    return render(request, 'presentar_pitch.html')


def registraralumnos(request):
    return cargar_alumnos(request)


# ===========================
# 🛒 MERCADO DE RETOS (100% mock, tokens en sesión)
# ===========================

def _get_challenge_catalog():
    """
    Catálogo mock de retos para el Market.
    NO toca la base de datos.
    """
    return {
        1: {
            "id": 1,
            "title": "Problema matemático",
            "description": "Dos integrantes resuelven un problema en 3 minutos.",
            "cost": 5,
        },
        2: {
            "id": 2,
            "title": "LEGO exprés",
            "description": "Prototipo con LEGO en 5 minutos.",
            "cost": 8,
        },
        3: {
            "id": 3,
            "title": "Pitch relámpago",
            "description": "Presentación de 60 segundos con idea clave.",
            "cost": 6,
        },
    }


def market_view(request):
    # Saldo temporal (luego se conectará con la BD)
    user_tokens = 12
    '''
    nota para el futuro
    para incorporar el saldo de tokens, tenemos que agarrar el grupo defininiendolo:
    grupo = (models.Grupo.objects.get(idgrupo=ID_DEL_GRUPO)), para esto sacamos el id del grupo tambien, lo podemos sacar con url
    si tenemos el id del grupo, cambiamos other_teams para que no muestre el mismo grupo
    (also asi)
    luego, usamos grupo.tokensgrupo en vez de 12 en user_tokens
    ya esta la logica de no dejar que se haga el reto de no tener suficientes tokens pero deberiamos integrar que reste los tokens al hacer el reto
    eso seria ! 
    - Sebastian (probablemente programara esto el pero documento esto por si alguien mas lo quiere hacer/para mi propio uso)
    '''

    # Catálogo de retos disponibles
    challenges = [
        {"id": 1, "title": "Problema matemático", "description": "Dos integrantes resuelven un problema en 3 minutos.", "cost": 5},
        {"id": 2, "title": "LEGO exprés", "description": "Prototipo con LEGO en 5 minutos.", "cost": 8},
        {"id": 3, "title": "Pitch relámpago", "description": "Presentación de 60 segundos con idea clave.", "cost": 6},
    ]

    other_teams = [
        {"id": 2, "name": "Equipo 2"},
        {"id": 3, "name": "Equipo 3"},
        {"id": 3, "name": "Equipo 4"},
    ]

    context = {
        "user_tokens": user_tokens,
        "challenges": challenges,
        "other_teams": other_teams,
    }
    return render(request, "market.html", context)


@require_http_methods(["POST"])
def issue_challenge_view(request, challenge_id):
    """
    Procesa la compra de un reto:
    - Usa el catálogo mock.
    - Descuenta tokens de la sesión.
    """
    catalog = _get_challenge_catalog()
    challenge_id = int(challenge_id)

    challenge = catalog.get(challenge_id)
    if not challenge:
        messages.error(request, "Reto no encontrado.")
        return redirect("market")

    target_team_id = request.POST.get("target_team_id")
    if not target_team_id:
        messages.error(request, "Selecciona un equipo objetivo.")
        return redirect("market")

    user_tokens = request.session.get("user_tokens", 12)
    cost = int(challenge["cost"])

    if user_tokens < cost:
        messages.error(request, "No tienes tokens suficientes.")
        return redirect("market")

    # Descontar y guardar en sesión
    user_tokens -= cost
    request.session["user_tokens"] = max(0, user_tokens)

    messages.success(
        request,
        f"Has retado al equipo {target_team_id} con “{challenge['title']}” por {cost} tokens. "
        f"Te quedan ahora {user_tokens} tokens."
    )
    return redirect("market")


# ===========================
# 🧩 EVALUACIÓN (Peer Review)
# ===========================

def peer_review_view(request, session_id=None):
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
        {"key": "presentacion", "label": "Presentación"},
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

    return render(request, "peer_review.html", context)


def rank_reflexion(request):
    return render(request, 'rank_reflexion.html')

def registrarprofesor(request):
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip()
        facultad = (request.POST.get("facultad") or "").strip()

        # Validaciones básicas
        if not email or not facultad:
            messages.error(request, "Completa todos los campos obligatorios.")
            return render(request, "registrarprofesor.html")

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "El correo no es válido.")
            return render(request, "registrarprofesor.html")

        # (Opcional) Forzar dominio UDD
        # if not email.lower().endswith("@udd.cl"):
        #     messages.error(request, "El correo debe ser institucional (@udd.cl).")
        #     return render(request, "registrarprofesor.html")

        # ¿Ya existe un profesor con ese email?
        if Profesor.objects.filter(emailprofesor=email).exists():
            messages.warning(request, "Ya existe un profesor con ese correo.")
            return render(request, "registrarprofesor.html")

        try:
            with transaction.atomic():
                # 1) Crear Usuario con password temporal (solo si tu diseño lo requiere)
                tmp_password = secrets.token_urlsafe(8)  # p.ej. 'V8Qx3r...'
                usuario = Usuario.objects.create(password=tmp_password)

                # 2) Crear Profesor asociado
                profesor = Profesor.objects.create(
                    usuario_idusuario=usuario,
                    emailprofesor=email,
                    facultad=facultad
                )

            messages.success(
                request,
                f"Profesor creado (ID {profesor.idprofesor}). Usuario ID {usuario.idusuario} asignado."
            )
            return redirect("dashboardadmin")  # o vuelve a la misma página si prefieres

        except Exception as e:
            messages.error(request, f"Ocurrió un error al guardar: {e}")
            return render(request, "registrarprofesor.html")

    # GET
    return render(request, "registrarprofesor.html")


def listar_profesores(request):
    profesores = Profesor.objects.all().order_by('-idprofesor')
    return render(request, 'listar_profesores.html', {'profesores': profesores})

@require_http_methods(["POST"])
def eliminar_profesor(request, idprofesor):
    profesor = get_object_or_404(Profesor, idprofesor=idprofesor)

    # Si tiene alumnos asociados, NO permitir borrar (FK bloquearía)
    if Alumno.objects.filter(profesor_idprofesor=profesor).exists():
        messages.error(request, "No se puede eliminar: el profesor tiene alumnos asociados.")
        return redirect('listar_profesores')

    try:
        with transaction.atomic():
            # Si quieres además eliminar el Usuario asociado (si no lo usa nadie más):
            usuario = profesor.usuario_idusuario
            profesor.delete()
            # Solo borra usuario si no hay otro profesor/relación apuntándolo
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
