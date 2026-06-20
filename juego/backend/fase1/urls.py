from django.urls import path
from . import views

urlpatterns = [
    path("pantalla_inicio/", views.pantalla_inicio, name="pantalla_inicio"),
    path("promptconocidos/", views.promptconocidos, name="promptconocidos"),
    path("conocidos-modo/<str:modo>/", views.elegir_modo_conocidos, name="elegir_modo_conocidos"),
    path("conocidos/", views.conocidos, name="conocidos"),
    path("conocidos-rapido/", views.conocidos_rapido, name="conocidos_rapido"),
    path("trabajoenequipo/", views.trabajoenequipo, name="trabajoenequipo"),
    path("minijuego1/", views.minijuego1, name="minijuego1"),
    path("sopa/registrar-palabra/", views.registrar_palabra_sopa, name="registrar_palabra_sopa"),
    path("sopa/completada/", views.sopa_completada, name="sopa_completada"),
]