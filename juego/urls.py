from django.urls import path
from . import views

urlpatterns = [
    path('', views.perfiles, name='perfiles'),
    path('registrarse/', views.registrarse, name='registrarse'),
    path('login/', views.login, name='login'),
    path('bienvenida/', views.bienvenida, name='bienvenida'),
    path('registro/', views.registro, name='registro'),
    path('lego/', views.lego, name='lego'),
    path('crearequipo/', views.crearequipo, name='crearequipo'),
    path('unirseequipo/', views.unirseequipo, name='unirseequipo'),
]
