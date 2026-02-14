from django.urls import path

from . import views

app_name = "consent"
urlpatterns = [
    path("", views.give_consent, name="give_consent"),
    path("declined/", views.decline_consent, name="declined"),
]
