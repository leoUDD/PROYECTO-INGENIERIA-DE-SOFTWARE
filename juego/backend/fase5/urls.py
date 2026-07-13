from django.urls import path
from . import views

urlpatterns = [
    path("peer-review/", views.peer_review_view, name="peer_review"),
    path("reflexion/", views.reflexion, name="reflexion"),

]