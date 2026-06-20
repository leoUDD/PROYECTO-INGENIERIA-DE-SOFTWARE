from django.urls import path
from . import views

urlpatterns = [
    path('transicioncreatividad/', views.transicioncreatividad, name='transicioncreatividad'),
    path('lego/', views.lego, name='lego'),
    path("ruleta-lego-token/", views.aplicar_resultado_ruleta_lego, name="aplicar_resultado_ruleta_lego"),


]