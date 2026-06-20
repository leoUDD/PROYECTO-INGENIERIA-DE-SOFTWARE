from django.urls import path
from . import views

urlpatterns = [
    path("ranking/", views.ranking_view, name="ranking"),
    path("grupo/<int:grupo_id>/listo-ranking/", views.marcar_listo_ranking, name="marcar_listo_ranking"),
]