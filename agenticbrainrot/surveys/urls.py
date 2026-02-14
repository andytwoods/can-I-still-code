from django.urls import path

from . import views

app_name = "surveys"
urlpatterns = [
    path("profile/intake/", views.profile_intake, name="profile_intake"),
]
