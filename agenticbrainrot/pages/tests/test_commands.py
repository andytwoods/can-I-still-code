from io import StringIO

import pytest
from allauth.account.models import EmailAddress
from allauth.account.models import EmailConfirmation
from django.contrib.auth import get_user_model
from django.core.management import call_command

User = get_user_model()


@pytest.mark.django_db
def test_setup_app_creates_superuser_and_sends_email():
    # Ensure no superuser exists
    assert not User.objects.filter(is_superuser=True).exists()

    out = StringIO()
    call_command("setup_app", stdout=out)

    # Check superuser created
    superuser = User.objects.get(is_superuser=True)
    assert superuser.email == "andytwoods@gmail.com"

    # Check EmailAddress created
    email_address = EmailAddress.objects.get(user=superuser, email=superuser.email)
    assert not email_address.verified
    assert email_address.primary

    # Check EmailConfirmation created
    assert EmailConfirmation.objects.filter(email_address=email_address).exists()

    # Run again, should skip
    out_skip = StringIO()
    call_command("setup_app", stdout=out_skip)
    assert "A superuser exists in the database. Skipping." in out_skip.getvalue()
