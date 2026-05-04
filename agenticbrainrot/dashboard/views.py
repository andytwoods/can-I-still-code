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
    "runs": "rgb(0, 158, 115)",
    "complexity": "rgb(204, 121, 167)",
    "efficiency": "rgb(86, 180, 233)",
    "accuracy_bg": "rgba(0, 114, 178, 0.1)",
    "speed_bg": "rgba(230, 159, 0, 0.1)",
    "runs_bg": "rgba(0, 158, 115, 0.1)",
    "complexity_bg": "rgba(204, 121, 167, 0.1)",
    "efficiency_bg": "rgba(86, 180, 233, 0.1)",
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
    runs_points = []
    complexity_points = []
    efficiency_points = []

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
                avg_runs=Avg("run_count"),
                avg_efficiency=Avg("efficiency_ratio"),
            )
            avg_accuracy = round(agg["avg_accuracy"] or 0, 1)
            avg_time = round(agg["avg_time"] or 0, 1)
            avg_runs = round(agg["avg_runs"] or 0, 1)
            avg_efficiency = round(agg["avg_efficiency"], 2) if agg["avg_efficiency"] is not None else None

            cyc_values = [
                a.complexity_metrics["cyclomatic_complexity"]
                for a in attempts
                if a.complexity_metrics and "cyclomatic_complexity" in a.complexity_metrics
            ]
            avg_complexity = round(sum(cyc_values) / len(cyc_values), 1) if cyc_values else None
        else:
            avg_accuracy = 0
            avg_time = 0
            avg_runs = 0
            avg_efficiency = None
            avg_complexity = None

        date_str = session.completed_at.strftime("%d %b %Y")

        session_rows.append(
            {
                "number": i,
                "date": date_str,
                "challenges_attempted": session.challenges_attempted,
                "avg_accuracy": avg_accuracy,
                "avg_time": avg_time,
                "avg_runs": avg_runs,
            },
        )
        accuracy_points.append({"x": i, "y": avg_accuracy, "date": date_str})
        speed_points.append({"x": i, "y": avg_time, "date": date_str})
        runs_points.append({"x": i, "y": avg_runs, "date": date_str})
        if avg_complexity is not None:
            complexity_points.append({"x": i, "y": avg_complexity, "date": date_str})
        if avg_efficiency is not None:
            efficiency_points.append({"x": i, "y": avg_efficiency, "date": date_str})

    return session_rows, accuracy_points, speed_points, runs_points, complexity_points, efficiency_points


@login_required
def personal_results(request):
    """Personal results dashboard for the participant."""
    participant = get_object_or_404(Participant, user=request.user)

    session_rows, accuracy_points, speed_points, runs_points, complexity_points, efficiency_points = _build_session_data(
        participant,
    )

    resumable_session = (
        CodeSession.objects.filter(
            participant=participant,
            status=CodeSession.Status.IN_PROGRESS,
        )
        .order_by("-started_at")
        .first()
    )

    context = {
        "session_rows": session_rows,
        "has_sessions": len(session_rows) > 0,
        "accuracy_data": json.dumps(accuracy_points),
        "speed_data": json.dumps(speed_points),
        "runs_data": json.dumps(runs_points),
        "complexity_data": json.dumps(complexity_points) if complexity_points else None,
        "loc_data": None,
        "efficiency_data": json.dumps(efficiency_points) if efficiency_points else None,
        "chart_colours": json.dumps(CHART_COLOURS),
        "resumable_session": resumable_session,
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
