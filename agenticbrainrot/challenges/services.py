import logging
import random

from django.conf import settings

from .models import Challenge
from .models import ChallengeAttempt

logger = logging.getLogger(__name__)

LOW_POOL_THRESHOLD = 20


class PoolExhaustedError(Exception):
    """Raised when no challenges remain for a participant."""


class LowPoolError(Exception):
    """Raised when challenge pool is getting low."""


def _get_available_by_tier(participant, tier_distribution, exclude_ids=()):
    """Return a shuffled pool of unseen challenge IDs keyed by tier."""
    seen_ids = set(
        ChallengeAttempt.objects.filter(
            participant=participant,
        ).values_list("challenge_id", flat=True),
    ) | set(exclude_ids)

    available = {}
    for tier_str in sorted(tier_distribution.keys()):
        tier = int(tier_str)
        pool = list(
            Challenge.objects.filter(difficulty=tier, is_active=True)
            .exclude(pk__in=seen_ids)
            .values_list("pk", flat=True)
        )
        random.shuffle(pool)
        available[tier] = pool
    return available


def select_challenges_for_session(participant):
    """
    Select the mandatory block of challenges: one per tier, ascending difficulty.

    Raises PoolExhaustedError if zero challenges remain across all tiers.
    """
    study = settings.STUDY
    tier_distribution = study["TIER_DISTRIBUTION"]

    available_by_tier = _get_available_by_tier(participant, tier_distribution)
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

    # Pick exactly 1 per tier (mandatory block)
    selected_ids = []
    for tier in sorted(available_by_tier.keys()):
        pool = available_by_tier[tier]
        if pool:
            selected_ids.append(pool[0])

    return list(
        Challenge.objects.filter(pk__in=selected_ids).order_by("difficulty"),
    )


def select_additional_challenges(participant, session, harder=False):
    """
    Select additional challenges after the mandatory block.

    If harder=True, prioritise higher tiers. Otherwise use the standard
    tier distribution. Returns challenges ordered ascending by difficulty,
    excluding anything already assigned to this session.
    """
    study = settings.STUDY
    tier_distribution = study["TIER_DISTRIBUTION"]
    challenges_per_session = study["CHALLENGES_PER_SESSION"]

    already_assigned = set(
        session.session_challenges.values_list("challenge_id", flat=True)
    )
    available_by_tier = _get_available_by_tier(
        participant, tier_distribution, exclude_ids=already_assigned
    )

    mandatory_count = session.session_challenges.count()
    remaining_slots = challenges_per_session - mandatory_count
    if wants_harder:
        remaining_slots = max(remaining_slots, 6)

    selected_ids = []

    if harder:
        # Fill from highest tiers first
        for tier in sorted(available_by_tier.keys(), reverse=True):
            if remaining_slots <= 0:
                break
            pool = available_by_tier[tier]
            take = min(remaining_slots, len(pool))
            selected_ids.extend(pool[:take])
            remaining_slots -= take
    else:
        # Standard distribution: pick according to tier weights
        for tier_str, count in sorted(tier_distribution.items()):
            if remaining_slots <= 0:
                break
            tier = int(tier_str)
            pool = available_by_tier.get(tier, [])
            take = min(count, len(pool), remaining_slots)
            selected_ids.extend(pool[:take])
            remaining_slots -= take

        # Top up from any remaining pool if short
        if remaining_slots > 0:
            for tier in sorted(available_by_tier.keys()):
                if remaining_slots <= 0:
                    break
                already_taken = set(selected_ids)
                extras = [pk for pk in available_by_tier[tier] if pk not in already_taken]
                take = min(remaining_slots, len(extras))
                selected_ids.extend(extras[:take])
                remaining_slots -= take

    return list(
        Challenge.objects.filter(pk__in=selected_ids).order_by("difficulty"),
    )
