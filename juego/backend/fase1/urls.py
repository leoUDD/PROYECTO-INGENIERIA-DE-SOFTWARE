from django.urls import path
from . import views

urlpatterns = [
    path("pantalla_inicio/", views.pantalla_inicio, name="pantalla_inicio"),
]