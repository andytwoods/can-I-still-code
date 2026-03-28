import json
import zipfile
from io import BytesIO
from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.db.models import F
from django.http import FileResponse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.utils import timezone

from agenticbrainrot.accounts.models import Participant
from agenticbrainrot.challenges.models import ChallengeAttempt
from agenticbrainrot.coding_sessions.models import CodeSession

from .models import DatasetAccessGrant

# Colourblind-friendly palette (Okabe-Ito)
CHART_COLOURS = {
    "accuracy": "rgb(0, 114, 178)",
    "speed": "rgb(230, 159, 0)",
    "accuracy_bg": "rgba(0, 114, 178, 0.1)",
    "speed_bg": "rgba(230, 159, 0, 0.1)",
}


def _build_session_data(participant):
    """Build session history and chart data for a participant."""
    sessions = CodeSession.objects.filter(
        participant=participant,
        status=CodeSession.Status.COMPLETED,
    ).order_by("completed_at")

    session_rows = []
    accuracy_points = []
    speed_points = []

    for i, session in enumerate(sessions, 1):
        attempts = ChallengeAttempt.objects.filter(
            session=session,
            skipped=False,
        )
        total_attempts = attempts.count()

        if total_attempts > 0:
            agg = attempts.aggregate(
                avg_accuracy=Avg(
                    F("tests_passed") * 100.0 / F("tests_total"),
                ),
                avg_time=Avg("time_taken_seconds"),
            )
            avg_accuracy = round(agg["avg_accuracy"] or 0, 1)
            avg_time = round(agg["avg_time"] or 0, 1)
        else:
            avg_accuracy = 0
            avg_time = 0

        label = f"Session {i}"
        date_str = session.completed_at.strftime("%d %b %Y")

        session_rows.append(
            {
                "number": i,
                "date": date_str,
                "challenges_attempted": session.challenges_attempted,
                "avg_accuracy": avg_accuracy,
                "avg_time": avg_time,
            },
        )
        accuracy_points.append({"x": label, "y": avg_accuracy})
        speed_points.append({"x": label, "y": avg_time})

    return session_rows, accuracy_points, speed_points


@login_required
def personal_results(request):
    """Personal results dashboard for the participant."""
    participant = get_object_or_404(Participant, user=request.user)

    session_rows, accuracy_points, speed_points = _build_session_data(
        participant,
    )

    context = {
        "session_rows": session_rows,
        "has_sessions": len(session_rows) > 0,
        "accuracy_data": json.dumps(accuracy_points),
        "speed_data": json.dumps(speed_points),
        "chart_colours": json.dumps(CHART_COLOURS),
    }

    return render(request, "dashboard/personal_results.html", context)


def _get_embargo_info():
    """Return embargo start date and whether embargo is active."""
    first_completed = (
        CodeSession.objects.filter(status=CodeSession.Status.COMPLETED)
        .order_by("completed_at")
        .values_list("completed_at", flat=True)
        .first()
    )
    if not first_completed:
        return None, True, None

    from datetime import timedelta  # noqa: PLC0415

    lift_date = first_completed + timedelta(days=365)
    is_active = timezone.now() < lift_date
    return first_completed, is_active, lift_date


def _get_available_versions():
    """List available dataset export versions."""
    exports_dir = Path("exports")
    if not exports_dir.exists():
        return []
    versions = []
    for d in sorted(exports_dir.iterdir(), reverse=True):
        if d.is_dir() and d.name.startswith("v"):
            manifest_path = d / "manifest.json"
            if manifest_path.exists():
                with manifest_path.open() as f:
                    manifest = json.load(f)
                versions.append(
                    {
                        "slug": d.name,
                        "exported_at": manifest.get("exported_at", ""),
                        "row_counts": manifest.get("row_counts", {}),
                    },
                )
    return versions


@login_required
def dataset_list(request):
    """Show available datasets and embargo status."""
    embargo_start, embargo_active, lift_date = _get_embargo_info()
    versions = _get_available_versions()

    has_grant = DatasetAccessGrant.objects.filter(
        user=request.user,
    ).exists()

    context = {
        "embargo_start": embargo_start,
        "embargo_active": embargo_active,
        "lift_date": lift_date,
        "versions": versions,
        "has_grant": has_grant,
        "can_download": not embargo_active or has_grant,
    }
    return render(request, "dashboard/dataset_list.html", context)


@login_required
def dataset_download(request, version):
    """Download a zipped dataset export."""
    _embargo_start, embargo_active, lift_date = _get_embargo_info()
    has_grant = DatasetAccessGrant.objects.filter(
        user=request.user,
    ).exists()

    if embargo_active and not has_grant:
        lift_str = lift_date.strftime("%d %B %Y") if lift_date else "TBD"
        return HttpResponse(
            f"Dataset is under embargo until {lift_str}. Contact the research team for early access.",
            status=403,
        )

    export_dir = Path("exports") / version
    if not export_dir.exists() or not (export_dir / "manifest.json").exists():
        return HttpResponse("Dataset version not found.", status=404)

    # Create zip in memory
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(export_dir.iterdir()):
            zf.write(f, f"{version}/{f.name}")
    buffer.seek(0)

    return FileResponse(
        buffer,
        as_attachment=True,
        filename=f"agenticbrainrot-{version}.zip",
        content_type="application/zip",
    )
