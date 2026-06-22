from django.urls import path
from . import views

urlpatterns = [
    path("transicioncomunicacion/", views.transicioncomunicacion, name="transicioncomunicacion"),
    path("guardar-pitch/", views.guardar_pitch, name="guardar_pitch"),
    path('pitch/', views.pitch, name='pitch'),
    path("orden-presentacion/", views.orden_presentacion_alumno, name="orden_presentacion_alumno"),
    path('presentar_pitch/', views.presentar_pitch, name='presentar_pitch'),
    path("sesion/<int:sesion_id>/iniciar-presentacion/", views.iniciar_presentacion_pitch, name="iniciar_presentacion_pitch"),
    path("sesion/<int:sesion_id>/siguiente-grupo-pitch/", views.siguiente_grupo_pitch, name="siguiente_grupo_pitch"),
]