from django.conf import settings
from django.core.cache import cache
from django.db.models import Avg
from django.db.models import Count
from django.db.models import F
from django.db.models import Max
from django.db.models import Subquery
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from agenticbrainrot.accounts.models import MetricEvent
from agenticbrainrot.accounts.models import Participant
from agenticbrainrot.challenges.models import ChallengeAttempt
from agenticbrainrot.coding_sessions.models import CodeSession
from agenticbrainrot.surveys.models import SurveyResponse

API_CACHE_TIMEOUT = 300  # 5 minutes
MIN_GROUP_SIZE = settings.STUDY.get("MIN_GROUP_SIZE_FOR_AGGREGATES", 10)

# Vibe-coding intensity thresholds
VIBE_LOW_THRESHOLD = 30
VIBE_HIGH_THRESHOLD = 70

# Common filters to exclude staff/superusers and withdrawn participants
_NON_STAFF_FILTER = {
    "participant__user__is_staff": False,
    "participant__user__is_superuser": False,
    "participant__withdrawn_at__isnull": True,
}


def stats_summary(request):
    """Total participants, sessions, and challenges solved."""
    cache_key = "api_stats_summary"
    data = cache.get(cache_key)
    if data is None:
        total_participants = Participant.objects.filter(
            has_active_consent=True,
            user__is_staff=False,
            user__is_superuser=False,
            withdrawn_at__isnull=True,
        ).count()

        completed_sessions = CodeSession.objects.filter(
            status=CodeSession.Status.COMPLETED,
            **_NON_STAFF_FILTER,
        )
        total_sessions = completed_sessions.count()
        total_challenges = (
            completed_sessions.aggregate(
                total=Sum("challenges_attempted"),
            )["total"]
            or 0
        )

        data = {
            "total_participants": total_participants,
            "total_sessions": total_sessions,
            "total_challenges_solved": total_challenges,
        }
        cache.set(cache_key, data, API_CACHE_TIMEOUT)

    return JsonResponse(data)


def stats_accuracy_over_time(request):
    """Average accuracy per month across all non-staff participants."""
    cache_key = "api_stats_accuracy_over_time"
    data = cache.get(cache_key)
    if data is None:
        monthly_with_counts = (
            ChallengeAttempt.objects.filter(
                skipped=False,
                tests_total__gt=0,
                **_NON_STAFF_FILTER,
            )
            .annotate(month=TruncMonth("started_at"))
            .values("month")
            .annotate(
                avg_accuracy=Avg(
                    F("tests_passed") * 100.0 / F("tests_total"),
                ),
                n_participants=Count(
                    "participant_id",
                    distinct=True,
                ),
            )
            .order_by("month")
        )

        data = {
            "months": [],
            "accuracy": [],
        }
        for row in monthly_with_counts:
            if row["n_participants"] >= MIN_GROUP_SIZE:
                data["months"].append(
                    row["month"].strftime("%Y-%m"),
                )
                data["accuracy"].append(
                    round(row["avg_accuracy"], 1),
                )

        cache.set(cache_key, data, API_CACHE_TIMEOUT)

    return JsonResponse(data)


def stats_accuracy_by_vibe_coding(request):
    """Accuracy over time, split by vibe-coding intensity."""
    cache_key = "api_stats_accuracy_by_vibe_coding"
    data = cache.get(cache_key)
    if data is None:
        # Get latest vibe_coding_pct response per participant
        # Subquery approach compatible with SQLite and PostgreSQL
        latest_ids = (
            SurveyResponse.objects.filter(
                question__category="vibe_coding_pct",
                question__context="post_session",
                participant__user__is_staff=False,
                participant__user__is_superuser=False,
                participant__withdrawn_at__isnull=True,
            )
            .values("participant_id")
            .annotate(latest_id=Max("id"))
            .values_list("latest_id", flat=True)
        )
        vibe_responses = SurveyResponse.objects.filter(
            id__in=Subquery(latest_ids),
        ).values_list("participant_id", "value")

        # Classify into low/medium/high
        groups = {"low": set(), "medium": set(), "high": set()}
        for pid, value in vibe_responses:
            try:
                pct = int(value)
            except ValueError, TypeError:
                continue
            if pct <= VIBE_LOW_THRESHOLD:
                groups["low"].add(pid)
            elif pct <= VIBE_HIGH_THRESHOLD:
                groups["medium"].add(pid)
            else:
                groups["high"].add(pid)

        data = {"groups": {}}

        for group_name, participant_ids in groups.items():
            if len(participant_ids) < MIN_GROUP_SIZE:
                continue

            monthly = (
                ChallengeAttempt.objects.filter(
                    participant_id__in=participant_ids,
                    skipped=False,
                    tests_total__gt=0,
                )
                .annotate(month=TruncMonth("started_at"))
                .values("month")
                .annotate(
                    avg_accuracy=Avg(
                        F("tests_passed") * 100.0 / F("tests_total"),
                    ),
                )
                .order_by("month")
            )

            months = []
            accuracy = []
            for row in monthly:
                months.append(row["month"].strftime("%Y-%m"))
                accuracy.append(round(row["avg_accuracy"], 1))

            data["groups"][group_name] = {
                "months": months,
                "accuracy": accuracy,
                "n_participants": len(participant_ids),
            }

        cache.set(cache_key, data, API_CACHE_TIMEOUT)

    return JsonResponse(data)


ALLOWED_CLIENT_METRICS = frozenset({"pyodide_load_failure"})


@require_POST
def report_client_metric(request):
    """Lightweight POST endpoint for client-side metric events."""
    event_type = request.POST.get("event_type", "")
    if event_type not in ALLOWED_CLIENT_METRICS:
        return JsonResponse({"error": "unknown event_type"}, status=400)
    MetricEvent.increment(event_type)
    return JsonResponse({"ok": True})
