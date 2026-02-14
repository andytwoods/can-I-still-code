from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404
from .models import Challenge
import json

@staff_member_required
def preview_challenge(request, challenge_id=None):
    """
    Staff-only view to preview a challenge in the code editor environment.
    """
    if challenge_id:
        challenge = get_object_or_404(Challenge, pk=challenge_id)
    else:
        challenge = Challenge.objects.filter(is_active=True).first()

    if not challenge:
        return render(request, "challenges/preview.html", {"error": "No challenges available."})

    context = {
        "challenge": challenge,
        "test_cases_json": json.dumps(challenge.test_cases),
        "is_preview": True,
    }
    return render(request, "challenges/preview.html", context)
