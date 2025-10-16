from django.shortcuts import redirect, render

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