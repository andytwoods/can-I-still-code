from django.urls import resolve
from django.urls import reverse

from agenticbrainrot.accounts.models import User


def test_detail(user: User):
    assert reverse("accounts:detail", kwargs={"pk": user.pk}) == f"/accounts/{user.pk}/"
    assert resolve(f"/accounts/{user.pk}/").view_name == "accounts:detail"


def test_update():
    assert reverse("accounts:update") == "/accounts/~update/"
    assert resolve("/accounts/~update/").view_name == "accounts:update"


def test_redirect():
    assert reverse("accounts:redirect") == "/accounts/~redirect/"
    assert resolve("/accounts/~redirect/").view_name == "accounts:redirect"
