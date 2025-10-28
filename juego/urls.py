# juego/urls.py
from django.urls import path
from . import views  # Importa todo el módulo views

urlpatterns = [
    path('', views.perfiles, name='perfiles'),
    path('registrarse/', views.registrarse, name='registrarse'),
    path('login/', views.login, name='login'),
    path('bienvenida/', views.bienvenida, name='bienvenida'),
    path('registro/', views.registro, name='registro'),
    path('lego/', views.lego, name='lego'),
    path('crearequipo/', views.crearequipo, name='crearequipo'),
    path('introducciones/', views.introducciones, name='introducciones'),
    path('pantalla_inicio/', views.pantalla_inicio, name='pantalla_inicio'),
    path('promptconocidos/', views.promptconocidos, name='promptconocidos'),
    path('conocidos/', views.conocidos, name='conocidos'),
    path('trabajoenequipo/', views.trabajoenequipo, name='trabajoenequipo'),
    path('minijuego1/', views.minijuego1, name='minijuego1'),
    path('tematicas/', views.tematicas, name='tematicas'),
    path('desafios/', views.desafios, name='desafios'),
    path('bubblemap/', views.bubblemap, name='bubblemap'),
    path('pitch/', views.pitch, name='pitch'),
    path('dashboardprofesor/', views.dashboardprofesor, name='dashboardprofesor'),
    path('registraralumnos/', views.registraralumnos, name='registraralumnos'),
    path('cargar-alumnos/', views.cargar_alumnos, name='cargar_alumnos'),
    path('agregar-alumnos/', views.agregar_alumno_manual, name='agregar_alumno_manual'),

    # Mercado de retos
    path('market/', views.market_view, name='market'),
    path('market/issue/<int:challenge_id>/', views.issue_challenge_view, name='issue_challenge'),

    # Peer review (usa la función definida en views.py)
    path('<int:session_id>/peer-review/', views.peer_review_view, name='peer_review'),
]

