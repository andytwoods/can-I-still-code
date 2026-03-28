from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from agenticbrainrot.accounts.models import Participant
from agenticbrainrot.accounts.models import User
from agenticbrainrot.coding_sessions.models import CodeSession
from agenticbrainrot.dashboard.models import DatasetAccessGrant


class TestDatasetList(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="data@example.com",
            password="testpass123",
        )
        self.participant, _ = Participant.objects.get_or_create(
            user=self.user,
        )
        self.participant.has_active_consent = True
        self.participant.save()

    def test_requires_login(self):
        url = reverse("dashboard:dataset_list")
        response = self.client.get(url)

        assert response.status_code == 302
        assert "login" in response.url.lower()

    def test_shows_page(self):
        self.client.force_login(self.user)
        url = reverse("dashboard:dataset_list")
        response = self.client.get(url)

        assert response.status_code == 200
        assert b"Research Datasets" in response.content

    def test_shows_embargo_info_when_no_sessions(self):
        self.client.force_login(self.user)
        url = reverse("dashboard:dataset_list")
        response = self.client.get(url)

        assert response.status_code == 200
        assert b"No sessions have been completed" in response.content


class TestDatasetDownload(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="download@example.com",
            password="testpass123",
        )
        self.participant, _ = Participant.objects.get_or_create(
            user=self.user,
        )

    def test_requires_login(self):
        url = reverse(
            "dashboard:dataset_download",
            kwargs={"version": "v2025-01-01"},
        )
        response = self.client.get(url)

        assert response.status_code == 302

    def test_returns_404_for_missing_version_post_embargo(self):
        """After embargo lifts, missing version returns 404."""
        self.participant.has_active_consent = True
        self.participant.save()
        # Create old completed session so embargo has lifted
        session = CodeSession.objects.create(
            participant=self.participant,
            status=CodeSession.Status.COMPLETED,
            completed_at=timezone.now() - timedelta(days=400),
        )
        CodeSession.objects.filter(pk=session.pk).update(
            started_at=timezone.now() - timedelta(days=400),
        )

        self.client.force_login(self.user)
        url = reverse(
            "dashboard:dataset_download",
            kwargs={"version": "v9999-01-01"},
        )
        response = self.client.get(url)

        assert response.status_code == 404

    def test_embargo_returns_403(self):
        """During embargo, user without grant gets 403."""
        # Create a completed session to set embargo start
        self.participant.has_active_consent = True
        self.participant.save()
        CodeSession.objects.create(
            participant=self.participant,
            status=CodeSession.Status.COMPLETED,
            completed_at=timezone.now(),
        )

        self.client.force_login(self.user)
        url = reverse(
            "dashboard:dataset_download",
            kwargs={"version": "v2025-01-01"},
        )
        response = self.client.get(url)

        assert response.status_code == 403

    def test_grant_bypasses_embargo(self):
        """User with DatasetAccessGrant can download during embargo."""
        self.participant.has_active_consent = True
        self.participant.save()
        CodeSession.objects.create(
            participant=self.participant,
            status=CodeSession.Status.COMPLETED,
            completed_at=timezone.now(),
        )

        DatasetAccessGrant.objects.create(
            user=self.user,
            granted_by=self.user,
            reason="Testing",
        )

        self.client.force_login(self.user)
        url = reverse(
            "dashboard:dataset_download",
            kwargs={"version": "v9999-01-01"},
        )
        response = self.client.get(url)

        # 404 because version doesn't exist, but NOT 403
        assert response.status_code == 404


class TestDatasetAccessGrant(TestCase):
    def test_str(self):
        user = User.objects.create_user(
            email="grant@example.com",
            password="testpass123",
        )
        grant = DatasetAccessGrant.objects.create(
            user=user,
            granted_by=user,
            reason="Test",
        )
        assert "grant@example.com" in str(grant)

    def test_str_without_user(self):
        grant = DatasetAccessGrant.objects.create(
            email="external@example.com",
            granted_by=None,
            reason="External",
        )
        assert "external@example.com" in str(grant)
