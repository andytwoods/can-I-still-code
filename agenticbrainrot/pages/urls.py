from django.urls import path

from .views import AboutView
from .views import HomeView
from .views import waitlist_signup
from .views import waitlist_unsubscribe

app_name = "pages"
urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("about/", AboutView.as_view(), name="about"),
    path("waitlist/", waitlist_signup, name="waitlist_signup"),
    path("waitlist/unsubscribe/<uuid:token>/", waitlist_unsubscribe, name="waitlist_unsubscribe"),
]
