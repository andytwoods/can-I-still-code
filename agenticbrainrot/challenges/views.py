import json

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import get_object_or_404
from django.shortcuts import render

from .models import Challenge


def preview_challenge(request, challenge_id=None):
    """
    Preview a challenge in the code editor. No data is saved.

    Access controlled by settings.LET_PEOPLE_TRY:
      - True: open to everyone
      - False: requires staff login
    """
    if not settings.LET_PEOPLE_TRY:
        if not request.user.is_staff:
            return redirect_to_login(request.get_full_path())
    all_challenges = Challenge.objects.filter(is_active=True).order_by(
        "difficulty",
        "title",
    )

    challenge = get_object_or_404(Challenge, pk=challenge_id) if challenge_id else all_challenges.first()

    if not challenge:
        return render(
            request,
            "challenges/preview.html",
            {"error": "No challenges available."},
        )

    # Build grouped list for the selector
    challenges_by_tier = {}
    ordered_ids = []
    for c in all_challenges:
        challenges_by_tier.setdefault(c.difficulty, []).append(c)
        ordered_ids.append(c.pk)

    # Find prev/next
    try:
        idx = ordered_ids.index(challenge.pk)
    except ValueError:
        idx = 0
    prev_id = ordered_ids[idx - 1] if idx > 0 else None
    next_id = ordered_ids[idx + 1] if idx < len(ordered_ids) - 1 else None

    context = {
        "challenge": challenge,
        "test_cases_json": json.dumps(challenge.test_cases),
        "is_preview": True,
        "challenges_by_tier": sorted(challenges_by_tier.items()),
        "prev_id": prev_id,
        "next_id": next_id,
        "current_position": idx + 1,
        "total_challenges": len(ordered_ids),
    }
    template = (
        "challenges/partials/_preview_content.html" if request.headers.get("HX-Request") else "challenges/preview.html"
    )
    return render(request, template, context)
