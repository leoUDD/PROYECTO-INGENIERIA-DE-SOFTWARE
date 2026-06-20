from django.urls import path
from . import views


urlpatterns = [
    path('transiciondesafio/', views.transiciondesafio, name='transiciondesafio'),
    path('tematicas/', views.tematicas, name='tematicas'),
    path("guardar-tematica/", views.guardar_tematica, name="guardar_tematica"),
    path('desafios/', views.desafios, name='desafios'),
    path("guardar-desafio/", views.guardar_desafio, name="guardar_desafio"),
    path("desbloquear-desafio/", views.desbloquear_desafio, name="desbloquear_desafio"),
    path('transicionempatia/', views.transicionempatia, name='transicionempatia'),
    path("bubblemap/", views.bubblemap, name="bubblemap"),
    path("bubblemap/otorgar-tokens/", views.otorgar_tokens_bubblemap, name="otorgar_tokens_bubblemap"),

]