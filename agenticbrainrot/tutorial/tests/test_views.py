from http import HTTPStatus

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from agenticbrainrot.accounts.models import Participant
from agenticbrainrot.accounts.models import User
from agenticbrainrot.consent.models import ConsentDocument
from agenticbrainrot.consent.models import ConsentRecord


@pytest.fixture
def consent_doc(db):
    return ConsentDocument.objects.create(
        version=1,
        title="T",
        body="B",
        is_active=True,
        published_at=timezone.now(),
    )


def _user(email):
    return User.objects.create_user(email=email, password="testpass123")


class TestTutorialView:
    def test_url_name_resolves(self):
        assert reverse("tutorial:index") == "/tutorial/"

    def test_anonymous_gets_page(self, db):
        response = Client().get(reverse("tutorial:index"))
        assert response.status_code == HTTPStatus.OK
        assert b"Python tutorial" in response.content

    def test_consented_user_gets_page(self, consent_doc):
        user = _user("consented@example.com")
        participant, _ = Participant.objects.get_or_create(user=user)
        ConsentRecord.objects.create(participant=participant, consent_document=consent_doc, consented=True)
        participant.has_active_consent = True
        participant.save(update_fields=["has_active_consent"])
        client = Client()
        client.force_login(user)
        response = client.get(reverse("tutorial:index"))
        assert response.status_code == HTTPStatus.OK

    def test_unconsented_user_is_not_redirected(self, consent_doc):
        user = _user("unconsented@example.com")
        Participant.objects.get_or_create(user=user)
        client = Client()
        client.force_login(user)
        response = client.get(reverse("tutorial:index"))
        assert response.status_code == HTTPStatus.OK

    def test_unconsented_user_is_still_gated_elsewhere(self, consent_doc):
        """Control: the exemption covers the tutorial only."""
        user = _user("gated@example.com")
        Participant.objects.get_or_create(user=user)
        client = Client()
        client.force_login(user)
        response = client.get(reverse("logged_in_home"))
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("consent:give_consent")

    def test_page_is_noindex(self, db):
        response = Client().get(reverse("tutorial:index"))
        assert b'content="noindex, nofollow"' in response.content

    def test_page_leaves_out_rollbar(self, db, settings):
        settings.ROLLBAR_CLIENT_TOKEN = "dummy-token"
        response = Client().get(reverse("tutorial:index"))
        assert b"rollbar" not in response.content.lower()

    def test_not_in_sitemap(self, db):
        response = Client().get(reverse("django.contrib.sitemaps.views.sitemap"))
        assert b"/tutorial/" not in response.content
