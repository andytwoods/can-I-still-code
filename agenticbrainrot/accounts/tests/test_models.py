from agenticbrainrot.accounts.models import User


def test_user_get_absolute_url(user: User):
    assert user.get_absolute_url() == f"/accounts/{user.pk}/"


def test_user_str(user: User):
    assert str(user) == user.email
