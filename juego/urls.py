from django.urls import include, path


urlpatterns = [
    # Acceso y sesión del grupo
    path("", include("juego.backend.acceso.urls")),

    # Gestión de profesores
    path("", include("juego.backend.profesor.urls")),

    # Creación y control de sesiones
    path("", include("juego.backend.sesiones.urls")),

    # Panel de administración
    path("", include("juego.backend.administracion.urls")),

    # Funciones globales y flujo compartido
    path("", include("juego.backend.core_global.urls")),

    # Fases del juego
    path("", include("juego.backend.fase1.urls")),
    path("", include("juego.backend.fase2.urls")),
    path("", include("juego.backend.fase3.urls")),
    path("", include("juego.backend.fase4.urls")),
    path("", include("juego.backend.fase5.urls")),

    # Ranking
    path("", include("juego.backend.ranking.urls")),
]