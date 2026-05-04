from http import HTTPStatus

import pytest
from django import forms as django_forms
from django.core.management import call_command
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from agenticbrainrot.accounts.models import Participant
from agenticbrainrot.accounts.models import User
from agenticbrainrot.consent.models import ConsentDocument
from agenticbrainrot.consent.models import ConsentRecord
from agenticbrainrot.surveys.forms import build_survey_form
from agenticbrainrot.surveys.models import SurveyQuestion
from agenticbrainrot.surveys.models import SurveyResponse

EXPECTED_PROFILE_QUESTIONS = 28
EXPECTED_POST_CHALLENGE_QUESTIONS = 4
EXPECTED_POST_SESSION_QUESTIONS = 9
EXPECTED_RESPONSE_COUNT = 2


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="intake@example.com",
        password="testpass123",
    )


@pytest.fixture
def participant(user):
    p, _ = Participant.objects.get_or_create(user=user)
    return p


@pytest.fixture
def consented_participant(participant):
    """Participant with active consent."""
    doc = ConsentDocument.objects.create(
        version=1,
        title="Test Consent",
        body="Test body",
        is_active=True,
        published_at=timezone.now(),
    )
    ConsentRecord.objects.create(
        participant=participant,
        consent_document=doc,
        consented=True,
    )
    participant.has_active_consent = True
    participant.save(update_fields=["has_active_consent"])
    return participant


@pytest.fixture
def authenticated_client(user):
    client = Client()
    client.login(
        email="intake@example.com",
        password="testpass123",
    )
    return client


@pytest.fixture
def profile_questions(db):
    """Create a small set of profile questions across two categories."""
    questions = []
    questions.append(
        SurveyQuestion.objects.create(
            text="What is your age range?",
            question_type="single_choice",
            choices=[["18-24", "18-24"], ["25-34", "25-34"]],
            context="profile",
            category="Demographics",
            is_required=True,
            display_order=1,
        ),
    )
    questions.append(
        SurveyQuestion.objects.create(
            text="Your country?",
            question_type="text",
            context="profile",
            category="Demographics",
            is_required=True,
            display_order=2,
        ),
    )
    questions.append(
        SurveyQuestion.objects.create(
            text="Python proficiency?",
            question_type="scale",
            scale_min=1,
            scale_max=5,
            min_label="Beginner",
            mid_label="Intermediate",
            max_label="Expert",
            context="profile",
            category="Experience",
            is_required=True,
            display_order=10,
        ),
    )
    return questions


class TestProfileIntakeView:
    def test_unauthenticated_redirected(self, db):
        client = Client()
        response = client.get(reverse("surveys:profile_intake"))
        assert response.status_code == HTTPStatus.FOUND

    def test_get_renders_first_category(
        self,
        authenticated_client,
        consented_participant,
        profile_questions,
    ):
        response = authenticated_client.get(
            reverse("surveys:profile_intake"),
        )
        assert response.status_code == HTTPStatus.OK
        assert b"Demographics" in response.content
        assert b"Step 1 of 2" in response.content

    def test_htmx_post_saves_and_advances(
        self,
        authenticated_client,
        consented_participant,
        profile_questions,
    ):
        """POST with HTMX saves responses and returns next step."""
        q1, q2, _q3 = profile_questions
        response = authenticated_client.post(
            reverse("surveys:profile_intake"),
            data={
                "step": "0",
                f"question_{q1.pk}": "18-24",
                f"question_{q2.pk}": "UK",
            },
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == HTTPStatus.OK
        assert b"Experience" in response.content
        assert b"Step 2 of 2" in response.content

        assert (
            SurveyResponse.objects.filter(
                participant=consented_participant,
            ).count()
            == EXPECTED_RESPONSE_COUNT
        )

    def test_final_step_completes_profile(
        self,
        authenticated_client,
        consented_participant,
        profile_questions,
    ):
        """Completing the last step sets profile_completed."""
        q1, q2, q3 = profile_questions

        # Step 1: Demographics
        authenticated_client.post(
            reverse("surveys:profile_intake"),
            data={
                "step": "0",
                f"question_{q1.pk}": "25-34",
                f"question_{q2.pk}": "US",
            },
            HTTP_HX_REQUEST="true",
        )

        # Step 2: Experience (final)
        response = authenticated_client.post(
            reverse("surveys:profile_intake"),
            data={
                "step": "1",
                f"question_{q3.pk}": "3",
            },
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == HTTPStatus.OK
        assert response["HX-Redirect"] == "/"

        consented_participant.refresh_from_db()
        assert consented_participant.profile_completed is True
        assert consented_participant.profile_updated_at is not None

    def test_validation_errors_re_render_step(
        self,
        authenticated_client,
        consented_participant,
        profile_questions,
    ):
        """Invalid data re-renders the current step with errors."""
        response = authenticated_client.post(
            reverse("surveys:profile_intake"),
            data={"step": "0"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == HTTPStatus.OK
        assert b"Demographics" in response.content

    def test_prefill_on_revisit(
        self,
        authenticated_client,
        consented_participant,
        profile_questions,
    ):
        """Revisiting pre-fills existing responses."""
        _q1, q2, _q3 = profile_questions

        SurveyResponse.objects.create(
            participant=consented_participant,
            question=q2,
            value="UK",
        )

        response = authenticated_client.get(
            reverse("surveys:profile_intake"),
        )
        assert response.status_code == HTTPStatus.OK
        assert b"UK" in response.content

    def test_edit_creates_superseding_response(
        self,
        authenticated_client,
        consented_participant,
        profile_questions,
    ):
        """Editing creates a new response that supersedes the old one."""
        q1, q2, _q3 = profile_questions

        # First submission
        authenticated_client.post(
            reverse("surveys:profile_intake"),
            data={
                "step": "0",
                f"question_{q1.pk}": "18-24",
                f"question_{q2.pk}": "UK",
            },
            HTTP_HX_REQUEST="true",
        )

        # Second submission (edit)
        authenticated_client.post(
            reverse("surveys:profile_intake"),
            data={
                "step": "0",
                f"question_{q1.pk}": "25-34",
                f"question_{q2.pk}": "France",
            },
            HTTP_HX_REQUEST="true",
        )

        q1_responses = SurveyResponse.objects.filter(
            participant=consented_participant,
            question=q1,
        ).order_by("answered_at")
        assert q1_responses.count() == EXPECTED_RESPONSE_COUNT
        latest = q1_responses.last()
        assert latest.supersedes == q1_responses.first()

    def test_no_questions_shows_message(
        self,
        authenticated_client,
        consented_participant,
    ):
        """If no profile questions exist, show an unavailable message."""
        response = authenticated_client.get(
            reverse("surveys:profile_intake"),
        )
        assert response.status_code == HTTPStatus.OK
        assert b"No profile questions" in response.content


class TestSeedCommand:
    def test_seed_creates_questions(self, db):
        call_command("seed_survey_questions")
        profile_count = SurveyQuestion.objects.filter(
            context="profile",
        ).count()
        assert profile_count == EXPECTED_PROFILE_QUESTIONS

        post_challenge_count = SurveyQuestion.objects.filter(
            context="post_challenge",
        ).count()
        assert post_challenge_count == EXPECTED_POST_CHALLENGE_QUESTIONS

        post_session_count = SurveyQuestion.objects.filter(
            context="post_session",
        ).count()
        assert post_session_count == EXPECTED_POST_SESSION_QUESTIONS

    def test_seed_idempotent(self, db):
        call_command("seed_survey_questions")
        first_count = SurveyQuestion.objects.count()
        call_command("seed_survey_questions")
        assert SurveyQuestion.objects.count() == first_count


class TestFormBuilder:
    def test_builds_all_field_types(self, db):
        text_q = SurveyQuestion.objects.create(
            text="Name?",
            question_type="text",
            context="profile",
            display_order=1,
        )
        number_q = SurveyQuestion.objects.create(
            text="Age?",
            question_type="number",
            context="profile",
            display_order=2,
        )
        sc_q = SurveyQuestion.objects.create(
            text="Fav?",
            question_type="single_choice",
            choices=[["a", "A"], ["b", "B"]],
            context="profile",
            display_order=3,
        )
        mc_q = SurveyQuestion.objects.create(
            text="Languages?",
            question_type="multi_choice",
            choices=[["py", "Python"], ["js", "JS"]],
            context="profile",
            display_order=4,
        )
        scale_q = SurveyQuestion.objects.create(
            text="Rate?",
            question_type="scale",
            scale_min=1,
            scale_max=5,
            context="profile",
            display_order=5,
        )

        qs = SurveyQuestion.objects.filter(
            pk__in=[text_q.pk, number_q.pk, sc_q.pk, mc_q.pk, scale_q.pk],
        )
        form_class = build_survey_form(qs)
        form = form_class()

        assert isinstance(
            form.fields[f"question_{text_q.pk}"],
            django_forms.CharField,
        )
        assert isinstance(
            form.fields[f"question_{number_q.pk}"],
            django_forms.IntegerField,
        )
        assert isinstance(
            form.fields[f"question_{sc_q.pk}"],
            django_forms.ChoiceField,
        )
        assert isinstance(
            form.fields[f"question_{mc_q.pk}"],
            django_forms.MultipleChoiceField,
        )
        assert isinstance(
            form.fields[f"question_{scale_q.pk}"],
            django_forms.IntegerField,
        )

    def test_form_validates_required(self, db):
        q = SurveyQuestion.objects.create(
            text="Required?",
            question_type="text",
            context="profile",
            is_required=True,
            display_order=1,
        )
        form_class = build_survey_form(
            SurveyQuestion.objects.filter(pk=q.pk),
        )
        form = form_class(data={})
        assert not form.is_valid()
        assert f"question_{q.pk}" in form.errors
