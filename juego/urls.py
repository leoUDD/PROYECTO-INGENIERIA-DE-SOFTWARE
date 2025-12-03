# juego/urls.py
from django.urls import path
from . import views  # Importa todo el módulo views

urlpatterns = [
    path('', views.perfiles, name='perfiles'),
    path('bienvenida/', views.bienvenida, name='bienvenida'),
    path('registro/', views.registro, name='registro'),
    path('lego/', views.lego, name='lego'),
    path('introducciones/', views.introducciones, name='introducciones'),
    path('pantalla_inicio/', views.pantalla_inicio, name='pantalla_inicio'),
    path('promptconocidos/', views.promptconocidos, name='promptconocidos'),
    path('conocidos/', views.conocidos, name='conocidos'),
    path('trabajoenequipo/', views.trabajoenequipo, name='trabajoenequipo'),
    path('minijuego1/', views.minijuego1, name='minijuego1'),
    path("sopa/completada/", views.sopa_completada, name="sopa_completada"),
    path('tematicas/', views.tematicas, name='tematicas'),
    path('desafios/', views.desafios, name='desafios'),
    path('bubblemap/', views.bubblemap, name='bubblemap'),
    path("orden-presentacion/", views.orden_presentacion_alumno, name="orden_presentacion_alumno"),
    path('pitch/', views.pitch, name='pitch'),
    path('presentar_pitch/', views.presentar_pitch, name='presentar_pitch'),
    path('dashboardprofesor/', views.dashboardprofesor, name='dashboardprofesor'),
    path('profesor/sesiones/', views.listar_sesiones, name='listar_sesiones'),
    path('profesor/sesiones/crear/', views.crear_sesion, name='crear_sesion'),
    path('registraralumnos/', views.registraralumnos, name='registraralumnos'),
    path('cargar-alumnos/', views.cargar_alumnos, name='cargar_alumnos'),
    path('agregar-alumnos/', views.agregar_alumno_manual, name='agregar_alumno_manual'),
    path('alumnos/eliminar/<int:idalumno>/', views.eliminar_alumno, name='eliminar_alumno'),
    path('profesores/', views.listar_profesores, name='listar_profesores'),
    path('profesores/eliminar/<int:idprofesor>/', views.eliminar_profesor, name='eliminar_profesor'),
    path('dashboardadmin/', views.dashboardadmin, name='dashboardadmin'),
    path('registrarprofesor/', views.registrarprofesor, name='registrarprofesor'),
    path('agregardesafio/', views.agregardesafio, name='agregardesafio'),
    path('listardesafios/', views.lista_desafios, name='lista_desafios'),
    path('desafios/<int:iddesafio>/eliminar/', views.eliminar_desafio, name='eliminar_desafio'),
    path('transicionempatia/', views.transicionempatia, name='transicionempatia'),
    path('transicioncreatividad/', views.transicioncreatividad, name='transicioncreatividad'),
    path('transicioncomunicacion/', views.transicioncomunicacion, name='transicioncomunicacion'),
    path('transiciondesafio/', views.transiciondesafio, name='transiciondesafio'),
    path('transicionapoyo/', views.transicionapoyo, name='transicionapoyo'),
    path('registrargrupos/', views.registrargrupos, name='registrargrupos'),


    # Mercado de retos
    path('market/', views.market_view, name='market'),
    path('market/issue/<int:challenge_id>/', views.issue_challenge_view, name='issue_challenge'),

    # Peer review (usa la función definida en views.py)
    path('peer-review/', views.peer_review_view, name='peer_review'),
    path("ranking/", views.ranking_view, name="ranking"),
    path('reflexion/', views.reflexion, name='reflexion'),
    path("mision-cumplida/", views.mision_cumplida_view, name="mision_cumplida"),

]

