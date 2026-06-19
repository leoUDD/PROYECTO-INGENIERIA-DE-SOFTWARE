from django.urls import path
from . import views

urlpatterns = [
    path("espera/", views.pantalla_espera, name="pantalla_espera"),
    path("sesion/<int:sesion_id>/estado/", views.estado_sesion, name="estado_sesion"),
    path("grupo/<int:grupo_id>/listo/", views.marcar_grupo_listo, name="marcar_grupo_listo"),
]