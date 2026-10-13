from django.urls import path

from agenticbrainrot.tutorial.views import TutorialView

app_name = "tutorial"

urlpatterns = [
    path("", TutorialView.as_view(), name="index"),
]
