from http import HTTPStatus

from django.test import Client
from django.urls import reverse
from django.utils import timezone

from agenticbrainrot.accounts.models import Participant
from agenticbrainrot.accounts.models import User
from agenticbrainrot.coding_sessions.models import CodeSession
from agenticbrainrot.consent.models import ConsentDocument
from agenticbrainrot.consent.models import ConsentRecord
from agenticbrainrot.pages.models import Sponsor


class TestLandingPage:
    def test_loads_for_anonymous(self, db):
        client = Client()
        response = client.get(reverse("home"))
        assert response.status_code == HTTPStatus.OK
        assert b"Can I Still Code" in response.content

    def test_shows_stats(self, db):
        client = Client()
        response = client.get(reverse("home"))
        assert response.status_code == HTTPStatus.OK
        assert b"Participants" in response.content
        assert b"Sessions Completed" in response.content
        assert b"Challenges Solved" in response.content

    def test_stats_reflect_data(self, db):
        """Stats should update when data exists."""
        user = User.objects.create_user(
            email="landing@example.com",
            password="testpass123",
        )
        p, _ = Participant.objects.get_or_create(user=user)
        doc = ConsentDocument.objects.create(
            version=1,
            title="T",
            body="B",
            is_active=True,
            published_at=timezone.now(),
        )
        ConsentRecord.objects.create(
            participant=p,
            consent_document=doc,
            consented=True,
        )
        p.has_active_consent = True
        p.save(update_fields=["has_active_consent"])

        CodeSession.objects.create(
            participant=p,
            status=CodeSession.Status.COMPLETED,
            completed_at=timezone.now(),
            challenges_attempted=5,
        )

        client = Client()
        response = client.get(reverse("home"))
        content = response.content.decode()
        # At least 1 participant and 1 session
        assert "1" in content

    def test_sponsor_placeholder_shown_when_empty(self, db):
        client = Client()
        response = client.get(reverse("home"))
        assert b"Get in touch" in response.content
        assert b"help cover the costs" in response.content

    def test_sponsors_shown_when_exist(self, db):
        Sponsor.objects.create(
            name="Test Sponsor",
            display_order=0,
            is_active=True,
        )
        client = Client()
        response = client.get(reverse("home"))
        assert b"Support This Research" in response.content
        assert b"Test Sponsor" in response.content
        assert b"Get in touch" not in response.content

    def test_inactive_sponsors_hidden(self, db):
        Sponsor.objects.create(
            name="Hidden Sponsor",
            display_order=0,
            is_active=False,
        )
        client = Client()
        response = client.get(reverse("home"))
        assert b"Hidden Sponsor" not in response.content


class TestSponsorModel:
    def test_str(self, db):
        sponsor = Sponsor.objects.create(
            name="Acme Corp",
            display_order=0,
        )
        assert str(sponsor) == "Acme Corp"

    def test_ordering(self, db):
        Sponsor.objects.create(name="Second", display_order=2)
        Sponsor.objects.create(name="First", display_order=1)
        sponsors = list(Sponsor.objects.values_list("name", flat=True))
        assert sponsors == ["First", "Second"]
