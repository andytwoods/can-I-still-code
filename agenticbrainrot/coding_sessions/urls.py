from django.urls import path

from . import views

app_name = "coding_sessions"
urlpatterns = [
    path(
        "sessions/start/",
        views.session_start,
        name="session_start",
    ),
    path(
        "sessions/<int:session_id>/",
        views.session_view,
        name="session_view",
    ),
]
