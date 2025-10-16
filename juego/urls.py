from django.urls import path
from . import views

urlpatterns = [
    path('', views.bienvenida, name='bienvenida'),
    path('registro/', views.registro, name='registro'),
    path('lego/', views.lego, name='lego'),
    path('crearequipo/', views.crearequipo, name='crearequipo'),
    path('unirseequipo/', views.unirseequipo, name='unirseequipo'),
    path('introducciones/', views.introducciones, name='introducciones'),
]
