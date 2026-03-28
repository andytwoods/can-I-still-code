import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from agenticbrainrot.accounts.models import User
from agenticbrainrot.challenges.models import Challenge
from agenticbrainrot.challenges.models import ChallengeAttempt
from agenticbrainrot.coding_sessions.models import CodeSession
from agenticbrainrot.surveys.models import SurveyQuestion
from agenticbrainrot.surveys.models import SurveyResponse


@pytest.fixture
def participant(db):
    from agenticbrainrot.accounts.models import Participant  # noqa: PLC0415

    user = User.objects.create_user(
        email="test@example.com",
        password="testpass123",
    )
    participant, _ = Participant.objects.get_or_create(user=user)
    return participant


@pytest.fixture
def profile_question(db):
    return SurveyQuestion.objects.create(
        text="What is your age?",
        question_type=SurveyQuestion.QuestionType.TEXT,
        context=SurveyQuestion.Context.PROFILE,
    )


@pytest.fixture
def post_challenge_question(db):
    return SurveyQuestion.objects.create(
        text="How did you feel?",
        question_type=SurveyQuestion.QuestionType.SCALE,
        context=SurveyQuestion.Context.POST_CHALLENGE,
        scale_min=1,
        scale_max=5,
    )


@pytest.fixture
def post_session_question(db):
    return SurveyQuestion.objects.create(
        text="Overall experience?",
        question_type=SurveyQuestion.QuestionType.SINGLE_CHOICE,
        context=SurveyQuestion.Context.POST_SESSION,
        choices=["Good", "OK", "Bad"],
    )


@pytest.fixture
def session(participant):
    return CodeSession.objects.create(participant=participant)


@pytest.fixture
def challenge(db):
    return Challenge.objects.create(
        external_id="test-challenge-v1",
        title="Test Challenge",
        description="A test",
        difficulty=1,
    )


@pytest.fixture
def attempt(participant, session, challenge):
    return ChallengeAttempt.objects.create(
        participant=participant,
        challenge=challenge,
        session=session,
    )


class TestSurveyResponseFKConstraints:
    """Test all 9 FK combinations (3 valid + 6 invalid)."""

    # --- 3 VALID cases ---

    def test_profile_both_null_valid(
        self,
        participant,
        profile_question,
    ):
        resp = SurveyResponse(
            participant=participant,
            question=profile_question,
            value="25",
        )
        resp.clean()
        resp.save()

    def test_post_session_with_session_valid(
        self,
        participant,
        post_session_question,
        session,
    ):
        resp = SurveyResponse(
            participant=participant,
            question=post_session_question,
            value="Good",
            session=session,
        )
        resp.clean()
        resp.save()

    def test_post_challenge_with_attempt_valid(
        self,
        participant,
        post_challenge_question,
        attempt,
    ):
        resp = SurveyResponse(
            participant=participant,
            question=post_challenge_question,
            value="3",
            challenge_attempt=attempt,
        )
        resp.clean()
        resp.save()

    # --- 6 INVALID cases ---

    def test_profile_with_session_invalid(
        self,
        participant,
        profile_question,
        session,
    ):
        resp = SurveyResponse(
            participant=participant,
            question=profile_question,
            value="25",
            session=session,
        )
        with pytest.raises(ValidationError):
            resp.clean()

    def test_profile_with_attempt_invalid(
        self,
        participant,
        profile_question,
        attempt,
    ):
        resp = SurveyResponse(
            participant=participant,
            question=profile_question,
            value="25",
            challenge_attempt=attempt,
        )
        with pytest.raises(ValidationError):
            resp.clean()

    def test_post_session_without_session_invalid(
        self,
        participant,
        post_session_question,
    ):
        resp = SurveyResponse(
            participant=participant,
            question=post_session_question,
            value="Good",
        )
        with pytest.raises(ValidationError):
            resp.clean()

    def test_post_session_with_attempt_invalid(
        self,
        participant,
        post_session_question,
        session,
        attempt,
    ):
        resp = SurveyResponse(
            participant=participant,
            question=post_session_question,
            value="Good",
            session=session,
            challenge_attempt=attempt,
        )
        with pytest.raises(ValidationError):
            resp.clean()

    def test_post_challenge_without_attempt_invalid(
        self,
        participant,
        post_challenge_question,
    ):
        resp = SurveyResponse(
            participant=participant,
            question=post_challenge_question,
            value="3",
        )
        with pytest.raises(ValidationError):
            resp.clean()

    def test_post_challenge_with_session_invalid(
        self,
        participant,
        post_challenge_question,
        session,
        attempt,
    ):
        resp = SurveyResponse(
            participant=participant,
            question=post_challenge_question,
            value="3",
            session=session,
            challenge_attempt=attempt,
        )
        with pytest.raises(ValidationError):
            resp.clean()


class TestSurveyResponseDBConstraint:
    """Test DB-level CheckConstraint prevents both FKs set."""

    def test_both_fks_set_rejected_at_db(
        self,
        participant,
        profile_question,
        session,
        attempt,
    ):
        with pytest.raises(IntegrityError):
            SurveyResponse.objects.create(
                participant=participant,
                question=profile_question,
                value="test",
                session=session,
                challenge_attempt=attempt,
            )
