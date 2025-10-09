# evaluation/urls.py
from django.urls import path
from .views import peer_review_view

app_name = "evaluation"

urlpatterns = [
    path("<int:session_id>/peer-review/", peer_review_view, name="peer_review"),
]

