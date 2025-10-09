from django.shortcuts import render

def bienvenida(request):
    return render(request, 'bienvenida.html')

def registro(request):
    return render(request, 'registro.html')

def lego(request):
    return render(request, 'lego.html')

def crearequipo(request):
    return render(request, 'crearequipo.html')

def unirseequipo(request):
    return render(request, 'unirseequipo.html')