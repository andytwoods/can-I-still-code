from django.urls import path

from .views import request_deletion
from .views import user_detail_view
from .views import user_redirect_view
from .views import user_update_view
from .views import withdraw

app_name = "accounts"
urlpatterns = [
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("~update/", view=user_update_view, name="update"),
    path("withdraw/", view=withdraw, name="withdraw"),
    path("request-deletion/", view=request_deletion, name="request_deletion"),
    path("<int:pk>/", view=user_detail_view, name="detail"),
]
