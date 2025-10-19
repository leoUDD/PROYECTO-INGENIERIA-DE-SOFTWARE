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
    path('introducciones/', views.introducciones, name='introducciones'),
    path('promptconocidos/', views.promptconocidos, name='promptconocidos'),
    path('conocidos/', views.conocidos, name='conocidos'),
    path('market/', views.market_view, name='market'),
    path('market/issue/<int:challenge_id>/', views.issue_challenge_view, name='issue_challenge'),
    path("<int:session_id>/peer-review/", peer_review_view, name="peer_review"),
]
