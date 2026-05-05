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


def select_challenges_for_session_full(participant):
    """
    Select the full session of challenges according to the tier distribution.
    1 mandatory block (one per tier) + additional challenges to reach CHALLENGES_PER_SESSION.
    """
    mandatory = select_challenges_for_session(participant)

    # We need a session object to use select_additional_challenges,
    # but that helper is designed to work with existing sessions.
    # For simple selection, let's just use the logic directly.

    study = settings.STUDY
    tier_distribution = study["TIER_DISTRIBUTION"]
    challenges_per_session = study["CHALLENGES_PER_SESSION"]

    selected_challenges = list(mandatory)
    already_assigned = {c.pk for c in selected_challenges}

    available_by_tier = _get_available_by_tier(
        participant, tier_distribution, exclude_ids=already_assigned
    )

    remaining_slots = challenges_per_session - len(selected_challenges)

    # Fill according to tier weights
    for tier_str, count in sorted(tier_distribution.items()):
        if remaining_slots <= 0:
            break
        tier = int(tier_str)
        pool = available_by_tier.get(tier, [])
        # Subtract what we already took for the mandatory block if it was from this tier
        # (Though mandatory is 1 per tier, and distribution counts might be higher)
        # Actually, let's just take 'count' more if available, up to remaining_slots.
        take = min(count, len(pool), remaining_slots)
        selected_challenges.extend(Challenge.objects.filter(pk__in=pool[:take]))
        already_assigned.update(pool[:take])
        remaining_slots -= take

    # Top up if still short
    if remaining_slots > 0:
        for tier in sorted(available_by_tier.keys()):
            if remaining_slots <= 0:
                break
            pool = available_by_tier[tier]
            extras = [pk for pk in pool if pk not in already_assigned]
            take = min(remaining_slots, len(extras))
            selected_challenges.extend(Challenge.objects.filter(pk__in=extras[:take]))
            already_assigned.update(extras[:take])
            remaining_slots -= take

    return sorted(selected_challenges, key=lambda c: c.difficulty)


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
    if harder:
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
