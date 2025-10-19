from django.shortcuts import redirect, render
from django.contrib import messages
from django.views.decorators.http import require_http_methods


# ===========================
# 📋 Vistas principales
# ===========================

def perfiles(request):
    return render(request, 'perfiles.html')


def registrarse(request):
    if request.method == 'POST':
        # Aquí se puede manejar la lógica de registro del usuario
        user_name = request.POST.get('user_name')
        email = request.POST.get('email')
        carrera = request.POST.get('carrera')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Validar que las contraseñas coincidan
        if password != confirm_password:
            error = 'Las contraseñas no coinciden'
            return render(request, 'registrarse.html', {'error': error})

        return redirect('login')
    return render(request, 'registrarse.html')


def login(request):
    if request.method == 'POST':
        # Aquí se puede manejar la lógica de autenticación del usuario
        email = request.POST.get('email')
        password = request.POST.get('password')
        # Autenticación (esto es solo un ejemplo, se debe implementar la lógica real)
        if email == 'leo@udd.cl' and password == '1234':
            return render(request, 'bienvenida.html', {'email': email})
        else:
            error = 'Credenciales inválidas'
            return render(request, 'login.html', {'error': error})

    return render(request, 'login.html')


def bienvenida(request):
    return render(request, 'bienvenida.html')


def registro(request):
    return render(request, 'registro.html')


def lego(request):
    return render(request, 'lego.html')


def crearequipo(request):
    return render(request, 'crearequipo.html')


def introducciones(request):
    return render(request, 'introducciones.html')


def promptconocidos(request):
    return render(request, 'promptconocidos.html')


def conocidos(request):
    return render(request, 'conocidos.html')


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

    return render(request, "juego/market.html", context)


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
