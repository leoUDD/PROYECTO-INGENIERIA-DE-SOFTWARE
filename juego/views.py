from django.shortcuts import render

def bienvenida(request):
    return render(request, 'bienvenida.html')

def registro(request):
    return render(request, 'registro.html')