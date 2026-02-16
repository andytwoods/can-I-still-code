from http import HTTPStatus

import pytest
from django.core.management import call_command
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from agenticbrainrot.accounts.models import Participant
from agenticbrainrot.accounts.models import User
from agenticbrainrot.challenges.models import Challenge
from agenticbrainrot.challenges.models import ChallengeAttempt
from agenticbrainrot.challenges.services import PoolExhaustedError
from agenticbrainrot.challenges.services import select_challenges_for_session
from agenticbrainrot.coding_sessions.models import CodeSession
from agenticbrainrot.coding_sessions.models import CodeSessionChallenge
from agenticbrainrot.consent.models import ConsentDocument
from agenticbrainrot.consent.models import ConsentRecord

EXPECTED_TOTAL_CHALLENGES = 150
EXPECTED_TIER_1 = 30
EXPECTED_TIER_2 = 30
EXPECTED_TIER_3 = 30
EXPECTED_TIER_4 = 30
EXPECTED_TIER_5 = 30
CHALLENGES_PER_SESSION = 10


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="challenge@example.com",
        password="testpass123",
    )


@pytest.fixture
def participant(user):
    p, _ = Participant.objects.get_or_create(user=user)
    return p


@pytest.fixture
def consented_participant(participant):
    doc = ConsentDocument.objects.create(
        version=1,
        title="Test",
        body="Body",
        is_active=True,
        published_at=timezone.now(),
    )
    ConsentRecord.objects.create(
        participant=participant,
        consent_document=doc,
        consented=True,
    )
    participant.has_active_consent = True
    participant.profile_completed = True
    participant.save(
        update_fields=["has_active_consent", "profile_completed"],
    )
    return participant


@pytest.fixture
def seeded_challenges(db):
    """Seed all challenges."""
    call_command("seed_challenges")
    return Challenge.objects.all()


@pytest.fixture
def small_challenge_set(db):
    """Create a small set of challenges for testing."""
    return [
        Challenge.objects.create(
            external_id=f"test-t{i}-{j}-v1",
            title=f"Test T{i} #{j}",
            description=f"Test challenge tier {i}",
            skeleton_code="def solution():\n    pass\n",
            test_cases=[
                {
                    "input": [],
                    "expected": True,
                    "description": "Test",
                },
            ],
            difficulty=i,
        )
        for i in range(1, 6)
        for j in range(3)
    ]


class TestSeedChallenges:
    def test_seed_creates_challenges(self, seeded_challenges):
        assert (
            seeded_challenges.count() == EXPECTED_TOTAL_CHALLENGES
        )

    def test_tier_distribution(self, seeded_challenges):
        assert (
            seeded_challenges.filter(difficulty=1).count()
            == EXPECTED_TIER_1
        )
        assert (
            seeded_challenges.filter(difficulty=2).count()
            == EXPECTED_TIER_2
        )
        assert (
            seeded_challenges.filter(difficulty=3).count()
            == EXPECTED_TIER_3
        )
        assert (
            seeded_challenges.filter(difficulty=4).count()
            == EXPECTED_TIER_4
        )
        assert (
            seeded_challenges.filter(difficulty=5).count()
            == EXPECTED_TIER_5
        )

    def test_idempotent(self, seeded_challenges):
        first_count = seeded_challenges.count()
        call_command("seed_challenges")
        assert Challenge.objects.count() == first_count

    def test_challenges_have_test_cases(self, seeded_challenges):
        for c in seeded_challenges:
            assert len(c.test_cases) > 0, (
                f"Challenge {c.external_id} has no test cases"
            )

    def test_challenges_have_skeleton_code(self, seeded_challenges):
        for c in seeded_challenges:
            assert c.skeleton_code.strip(), (
                f"Challenge {c.external_id} has no skeleton code"
            )

    def test_test_cases_hash_populated(self, seeded_challenges):
        for c in seeded_challenges:
            assert c.test_cases_hash, (
                f"Challenge {c.external_id} has no test_cases_hash"
            )


class TestChallengeSelection:
    def test_selects_correct_count(
        self, consented_participant, small_challenge_set,
    ):
        selected = select_challenges_for_session(
            consented_participant,
        )
        assert len(selected) == CHALLENGES_PER_SESSION

    def test_ascending_difficulty(
        self, consented_participant, small_challenge_set,
    ):
        selected = select_challenges_for_session(
            consented_participant,
        )
        difficulties = [c.difficulty for c in selected]
        assert difficulties == sorted(difficulties)

    def test_no_repeats(
        self, consented_participant, small_challenge_set,
    ):
        selected = select_challenges_for_session(
            consented_participant,
        )
        ids = [c.pk for c in selected]
        assert len(ids) == len(set(ids))

    def test_excludes_already_seen(
        self, consented_participant, small_challenge_set,
    ):
        """Challenges already attempted are excluded."""
        session = CodeSession.objects.create(
            participant=consented_participant,
        )
        first_selection = select_challenges_for_session(
            consented_participant,
        )
        # Mark first selection as attempted
        for i, challenge in enumerate(first_selection):
            CodeSessionChallenge.objects.create(
                session=session,
                challenge=challenge,
                position=i,
            )
            ChallengeAttempt.objects.create(
                participant=consented_participant,
                challenge=challenge,
                session=session,
                skipped=True,
            )

        second_selection = select_challenges_for_session(
            consented_participant,
        )
        first_ids = {c.pk for c in first_selection}
        second_ids = {c.pk for c in second_selection}
        assert first_ids.isdisjoint(second_ids)

    def test_pool_exhaustion_raises(
        self, consented_participant, db,
    ):
        """When no challenges remain, PoolExhaustedError is raised."""
        # No challenges in DB
        with pytest.raises(PoolExhaustedError):
            select_challenges_for_session(consented_participant)

    def test_partial_pool_returns_fewer(
        self, consented_participant, db,
    ):
        """When fewer than 10 challenges are available, returns what's available."""
        for i in range(3):
            Challenge.objects.create(
                external_id=f"sparse-{i}-v1",
                title=f"Sparse {i}",
                description="Test",
                skeleton_code="pass",
                test_cases=[{"input": [], "expected": True, "description": "t"}],
                difficulty=1,
            )
        selected = select_challenges_for_session(
            consented_participant,
        )
        expected_sparse_count = 3
        assert len(selected) == expected_sparse_count

    def test_tier_fill_from_adjacent(
        self, consented_participant, db,
    ):
        """When a tier is exhausted, fills from adjacent tiers."""
        # Only create tier 1 challenges (no tier 2-5)
        for i in range(CHALLENGES_PER_SESSION):
            Challenge.objects.create(
                external_id=f"only-t1-{i}-v1",
                title=f"T1 #{i}",
                description="Test",
                skeleton_code="pass",
                test_cases=[{"input": [], "expected": True, "description": "t"}],
                difficulty=1,
            )
        selected = select_challenges_for_session(
            consented_participant,
        )
        assert len(selected) == CHALLENGES_PER_SESSION
        assert all(c.difficulty == 1 for c in selected)


class TestSessionView:
    def test_session_view_requires_auth(self, db):
        client = Client()
        response = client.get(
            reverse(
                "coding_sessions:session_view",
                kwargs={"session_id": 1},
            ),
        )
        assert response.status_code == HTTPStatus.FOUND

    def test_session_view_forbidden_for_other_user(
        self, consented_participant, small_challenge_set,
    ):
        """Cannot view another participant's session."""
        session = CodeSession.objects.create(
            participant=consented_participant,
        )
        # Create another consented user
        other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123",
        )
        other_p, _ = Participant.objects.get_or_create(user=other_user)
        doc = ConsentDocument.objects.filter(is_active=True).first()
        if doc:
            ConsentRecord.objects.create(
                participant=other_p,
                consent_document=doc,
                consented=True,
            )
        other_p.has_active_consent = True
        other_p.save(update_fields=["has_active_consent"])

        client = Client()
        client.login(
            email="other@example.com",
            password="testpass123",
        )
        response = client.get(
            reverse(
                "coding_sessions:session_view",
                kwargs={"session_id": session.pk},
            ),
        )
        assert response.status_code == HTTPStatus.FORBIDDEN
