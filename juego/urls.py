# juego/urls.py
from juego.backend.fase4 import views as fase4_views
from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    #ORDENAMIENTO
    path("", include("juego.backend.core_global.urls")),
    path("", include("juego.backend.fase1.urls")),
    path("", include("juego.backend.fase2.urls")),
    path("", include("juego.backend.fase3.urls")),
    path("", include("juego.backend.fase4.urls")),
    path("", include("juego.backend.fase5.urls")),
    path("", include("juego.backend.ranking.urls")),
    #FIN ORDENAMIENTO
    
    #NUEVO
    path(
    "sesion/<int:sesion_id>/dev/timer-10/",
    views.dev_timer_10_segundos,
    name="dev_timer_10_segundos"
    ),
    path("continuar-desde-mapa/", views.continuar_desde_mapa, name="continuar_desde_mapa"),
    path("sesion/<int:sesion_id>/fase-anterior/", views.profesor_fase_anterior, name="profesor_fase_anterior"),
    path("dashboardadmin/tiempos/", views.admin_tiempos, name="admin_tiempos"),
    path("dashboardadmin/ruleta/", views.admin_ruleta, name="admin_ruleta"),
    path("ver-grupo/<int:grupo_id>/", views.ver_como_grupo, name="ver_como_grupo"),
    path("dashboardadmin/desafios/<int:desafio_id>/info/", views.admin_desafio_info, name="admin_desafio_info"),
    path("profesores/", views.registrarprofesor, name="listar_profesores"),
    path("profesor/<int:profesor_id>/eliminar/", views.eliminar_profesor, name="eliminar_profesor"),
    path("profesor/<int:profesor_id>/eliminar-forzado/", views.eliminar_profesor_forzado, name="eliminar_profesor_forzado"),
    path("sesion/<int:sesion_id>/iniciar-timer-inicio-fase/", views.iniciar_timer_inicio_fase, name="iniciar_timer_inicio_fase"),
    path("presentar-pitch/", fase4_views.presentar_pitch, name="presentar_pitch"),
    path("habilidades-intro/", views.habilidades_intro, name="habilidades_intro"),
    path('dashboardadmin/tematicas/', views.admin_tematicas, name='admin_tematicas'),
    path('dashboardadmin/desafios/', views.admin_desafios, name='admin_desafios'),
    path("cambiar-tematica/", views.cambiar_tematica, name="cambiar_tematica"),
    path("sesion/<int:sesion_id>/actualizar-estado/", views.profesor_actualizar_estado, name="profesor_actualizar_estado"),
    path("sesion/<int:sesion_id>/siguiente-fase/", views.profesor_siguiente_fase, name="profesor_siguiente_fase"),
    path("finalizar-mision/", views.finalizar_mision, name="finalizar_mision"),
    path("salir/", views.salir_grupo, name="salir_grupo"),
    path("sesion/<int:sesion_id>/control/", views.control_sesion, name="control_sesion"),
    path("sesion/<int:sesion_id>/preview/", views.preview_pantalla_profesor, name="preview_pantalla_profesor"),
    path("espera-eleccion/", views.espera_eleccion, name="espera_eleccion"),

path(
    "sesion/<int:sesion_id>/estado-presentacion/",
    fase4_views.estado_presentacion_pitch,
    name="estado_presentacion_pitch",
),

    #NUEVO CIERRE 


    path('', views.perfiles, name='perfiles'),
    path('bienvenida/', views.bienvenida, name='bienvenida'),
    path('registro/', views.registro, name='registro'),
    path('introducciones/', views.introducciones, name='introducciones'),
    path('dashboardprofesor/', views.dashboardprofesor, name='dashboardprofesor'),
    path('profesor/sesiones/', views.listar_sesiones, name='listar_sesiones'),
    path('profesor/sesiones/crear/', views.crear_sesion, name='crear_sesion'),
    path('registraralumnos/', views.registraralumnos, name='registraralumnos'),
    path('cargar-alumnos/', views.cargar_alumnos, name='cargar_alumnos'),
    path('agregar-alumnos/', views.agregar_alumno_manual, name='agregar_alumno_manual'),
    path('alumnos/eliminar/<int:idalumno>/', views.eliminar_alumno, name='eliminar_alumno'),
    path('dashboardadmin/', views.dashboardadmin, name='dashboardadmin'),
    path('registrarprofesor/', views.registrarprofesor, name='registrarprofesor'),
    path('agregardesafio/', views.agregardesafio, name='agregardesafio'),
    path('listardesafios/', views.lista_desafios, name='lista_desafios'),
    path('desafios/<int:iddesafio>/eliminar/', views.eliminar_desafio, name='eliminar_desafio'),
    path('transicionapoyo/', views.transicionapoyo, name='transicionapoyo'),
    path('registrargrupos/', views.registrargrupos, name='registrargrupos'),
    path('market/', views.market_view, name='market'),
    path('market/issue/<int:challenge_id>/', views.issue_challenge_view, name='issue_challenge'),
    path('reflexion/', views.reflexion, name='reflexion'),
    path("mision-cumplida/", views.mision_cumplida_view, name="mision_cumplida"),

]

