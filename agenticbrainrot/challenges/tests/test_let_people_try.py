from http import HTTPStatus

import pytest
from django.test import Client
from django.test import override_settings
from django.urls import reverse

from agenticbrainrot.accounts.models import User
from agenticbrainrot.challenges.models import Challenge


@pytest.fixture
def challenge(db):
    return Challenge.objects.create(
        external_id="try-test-v1",
        title="Try Test",
        description="A test challenge",
        skeleton_code="def solution():\n    pass\n",
        test_cases=[{"input": [], "expected": True, "description": "Test"}],
        difficulty=1,
    )


@pytest.fixture
def staff_client(db):
    User.objects.create_user(
        email="staff@example.com",
        password="testpass123",
        is_staff=True,
    )
    client = Client()
    client.login(email="staff@example.com", password="testpass123")
    return client


@pytest.fixture
def anon_client():
    return Client()


class TestPreviewAccessWhenDisabled:
    """Preview at /challenges/preview/ should require staff when LET_PEOPLE_TRY=False."""

    @override_settings(LET_PEOPLE_TRY=False)
    def test_anon_redirected_to_login(self, anon_client, challenge):
        response = anon_client.get(reverse("challenges:preview_challenge"))
        assert response.status_code == HTTPStatus.FOUND
        assert "login" in response.url

    @override_settings(LET_PEOPLE_TRY=False)
    def test_staff_can_access(self, staff_client, challenge):
        response = staff_client.get(reverse("challenges:preview_challenge"))
        assert response.status_code == HTTPStatus.OK


class TestPreviewAccessWhenEnabled:
    """Preview should be open to everyone when LET_PEOPLE_TRY=True."""

    @override_settings(LET_PEOPLE_TRY=True)
    def test_anon_can_access(self, anon_client, challenge):
        response = anon_client.get(reverse("challenges:preview_challenge"))
        assert response.status_code == HTTPStatus.OK

    @override_settings(LET_PEOPLE_TRY=True)
    def test_staff_can_access(self, staff_client, challenge):
        response = staff_client.get(reverse("challenges:preview_challenge"))
        assert response.status_code == HTTPStatus.OK


class TestMockSessionAccessWhenDisabled:
    """Mock session at /sessions/mock/ should require staff when LET_PEOPLE_TRY=False."""

    @override_settings(LET_PEOPLE_TRY=False)
    def test_anon_get_redirected_to_login(self, anon_client):
        response = anon_client.get(reverse("coding_sessions:mock_session_start"))
        assert response.status_code == HTTPStatus.FOUND
        assert "login" in response.url

    @override_settings(LET_PEOPLE_TRY=False)
    def test_anon_post_redirected_to_login(self, anon_client):
        response = anon_client.post(
            reverse("coding_sessions:mock_session_start"),
            {"device_type": "desktop"},
        )
        assert response.status_code == HTTPStatus.FOUND
        assert "login" in response.url

    @override_settings(LET_PEOPLE_TRY=False)
    def test_staff_can_access(self, staff_client):
        response = staff_client.get(reverse("coding_sessions:mock_session_start"))
        assert response.status_code == HTTPStatus.OK


class TestMockSessionAccessWhenEnabled:
    """Mock session should be open to everyone when LET_PEOPLE_TRY=True."""

    @override_settings(LET_PEOPLE_TRY=True)
    def test_anon_can_access(self, anon_client):
        response = anon_client.get(reverse("coding_sessions:mock_session_start"))
        assert response.status_code == HTTPStatus.OK

    @override_settings(LET_PEOPLE_TRY=True)
    def test_staff_can_access(self, staff_client):
        response = staff_client.get(reverse("coding_sessions:mock_session_start"))
        assert response.status_code == HTTPStatus.OK
