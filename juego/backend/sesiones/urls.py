from django.urls import path

from juego.backend.sesiones import views


urlpatterns = [
    path("registraralumnos/", views.registraralumnos, name="registraralumnos",),
]