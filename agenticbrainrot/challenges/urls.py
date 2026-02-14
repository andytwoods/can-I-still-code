
from django.urls import path
from . import views

app_name = "challenges"
urlpatterns = [
    path("preview/", views.preview_challenge, name="preview_challenge"),
    path("preview/<int:challenge_id>/", views.preview_challenge, name="preview_challenge_detail"),
]
