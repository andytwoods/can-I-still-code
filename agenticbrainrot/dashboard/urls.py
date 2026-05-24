from django.urls import path

from . import views

app_name = "dashboard"
urlpatterns = [
    path(
        "stats/",
        views.study_stats,
        name="study_stats",
    ),
    path(
        "results/",
        views.personal_results,
        name="personal_results",
    ),
    path(
        "data/",
        views.dataset_list,
        name="dataset_list",
    ),
    path(
        "data/download/<str:version>/",
        views.dataset_download,
        name="dataset_download",
    ),
]
