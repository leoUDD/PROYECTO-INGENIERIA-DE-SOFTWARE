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

        return redirect('pantalla_inicio')  # <-- ajusta al name de tu URL real

    return render(request, 'registro.html', {'error': error})



def trabajoenequipo(request):
    return render(request, 'trabajoenequipo.html')


def lego(request):
    return render(request, 'lego.html')


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


def tematicas(request):
    return render(request, 'tematicas.html')


def dashboardprofesor(request):
    return render(request, 'dashboardprofesor.html')


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
    return render(request, 'transicionempatia.html')


def transicioncreatividad(request):
    return render(request, 'transicioncreatividad.html')


def transicioncomunicacion(request):
    return render(request, 'transicioncomunicacion.html')


def transiciondesafio(request):
    return render(request, 'transiciondesafio.html')


def transicionapoyo(request):
    return render(request, 'transicionapoyo.html')

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
    return render(request, 'pitch.html')


def presentar_pitch(request):
    return render(request, 'presentar_pitch.html')


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
            nombre=nombre
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