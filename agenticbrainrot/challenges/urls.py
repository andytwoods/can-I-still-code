from django.urls import path

from . import views

app_name = "challenges"
urlpatterns = [
    path(
        "preview/",
        views.preview_challenge,
        name="preview_challenge",
    ),
    path(
        "preview/<int:challenge_id>/",
        views.preview_challenge,
        name="preview_challenge_detail",
    ),
    path(
        "preview/<slug:external_id>/",
        views.preview_challenge_by_external_id,
        name="preview_challenge_by_external_id",
    ),
    path(
        "<int:challenge_id>/report/",
        views.report_challenge,
        name="report_challenge",
    ),
]
