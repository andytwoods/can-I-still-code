import logging

from django.conf import settings

from .models import Challenge
from .models import ChallengeAttempt

logger = logging.getLogger(__name__)

LOW_POOL_THRESHOLD = 20


class PoolExhaustedError(Exception):
    """Raised when no challenges remain for a participant."""


class LowPoolError(Exception):
    """Raised when challenge pool is getting low."""


def select_challenges_for_session(participant):
    """
    Select challenges for a new session based on STUDY settings.

    Returns an ordered list of Challenge objects (ascending difficulty).

    Raises PoolExhaustedError if zero challenges remain.
    Logs a warning if pool drops below LOW_POOL_THRESHOLD.
    """
    study = settings.STUDY
    tier_distribution = study["TIER_DISTRIBUTION"]
    challenges_per_session = study["CHALLENGES_PER_SESSION"]

    seen_ids = set(
        ChallengeAttempt.objects.filter(
            participant=participant,
        ).values_list("challenge_id", flat=True),
    )

    # Get available unseen challenges by tier
    available_by_tier = {}
    for tier_str in sorted(tier_distribution.keys()):
        tier = int(tier_str)
        qs = Challenge.objects.filter(difficulty=tier, is_active=True).exclude(pk__in=seen_ids)
        available_by_tier[tier] = list(qs.values_list("pk", flat=True))

    total_available = sum(len(v) for v in available_by_tier.values())

    if total_available == 0:
        msg = "No challenges remaining for this participant."
        raise PoolExhaustedError(msg)

    if total_available < LOW_POOL_THRESHOLD:
        logger.warning(
            "Low challenge pool for participant %s: %d remaining",
            participant.pk,
            total_available,
        )

    # Select challenges according to tier distribution
    selected_ids = []

    # First pass: pick from each tier according to distribution
    for tier_str, count in sorted(tier_distribution.items()):
        tier = int(tier_str)
        pool = available_by_tier.get(tier, [])
        take = min(count, len(pool))
        selected_ids.extend(pool[:take])
        # Remove selected from pool
        available_by_tier[tier] = pool[take:]

    # If we haven't reached the target, fill from adjacent tiers
    if len(selected_ids) < challenges_per_session:
        remaining_needed = challenges_per_session - len(selected_ids)
        # Try filling from tiers with remaining challenges,
        # starting from lower tiers
        for tier in sorted(available_by_tier.keys()):
            pool = available_by_tier[tier]
            if not pool:
                continue
            take = min(remaining_needed, len(pool))
            selected_ids.extend(pool[:take])
            remaining_needed -= take
            if remaining_needed <= 0:
                break

    # Cap at challenges_per_session
    selected_ids = selected_ids[:challenges_per_session]

    # Fetch challenge objects and sort by ascending difficulty
    return list(
        Challenge.objects.filter(pk__in=selected_ids).order_by("difficulty"),
    )
