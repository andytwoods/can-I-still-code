import csv
import hashlib
import hmac
import json
import subprocess
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from django.conf import settings
from django.utils import timezone

from agenticbrainrot.accounts.models import log_audit_event


def _anon_id(pk):
    """Map participant PK to a stable opaque ID via HMAC-SHA256."""
    key = settings.EXPORT_SECRET_KEY.encode()
    return hmac.new(key, str(pk).encode(), hashlib.sha256).hexdigest()[:16]


def _date_only(dt):
    """Coarsen a datetime to date string, or empty string if None."""
    if dt is None:
        return ""
    return dt.date().isoformat()


def _git_hash():
    """Get current git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except FileNotFoundError:
        return "unknown"


def _sha256_file(path):
    """Compute SHA-256 checksum of a file."""
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_csv(path, headers, rows):
    """Write rows to CSV file."""
    with Path(path).open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    return len(rows)


def _write_parquet(path, headers, rows):
    """Write rows to Parquet file."""
    columns = {h: [] for h in headers}
    for row in rows:
        for h, val in zip(headers, row, strict=True):
            columns[h].append(val)
    table = pa.table(columns)
    pq.write_table(table, path)


def _build_rows(queryset, row_fn):
    """Build rows list from queryset using row_fn."""
    return [row_fn(obj) for obj in queryset]


def export_participants(output_dir):
    """Export anonymised participant data."""
    from agenticbrainrot.accounts.models import Participant  # noqa: PLC0415

    participants = Participant.objects.filter(
        withdrawn_at__isnull=True,
        user__is_staff=False,
        user__is_superuser=False,
    ).select_related("user")

    headers = [
        "participant_id",
        "has_active_consent",
        "profile_completed",
        "profile_updated_at",
    ]
    rows = _build_rows(
        participants,
        lambda p: [
            _anon_id(p.pk),
            p.has_active_consent,
            p.profile_completed,
            _date_only(p.profile_updated_at),
        ],
    )

    count = _write_csv(output_dir / "participants.csv", headers, rows)
    _write_parquet(output_dir / "participants.parquet", headers, rows)
    return count


def export_code_sessions(output_dir):
    """Export code session data."""
    from agenticbrainrot.coding_sessions.models import CodeSession  # noqa: PLC0415

    sessions = CodeSession.objects.filter(
        participant__withdrawn_at__isnull=True,
        participant__user__is_staff=False,
        participant__user__is_superuser=False,
    ).select_related("participant")

    headers = [
        "session_id",
        "participant_id",
        "status",
        "started_at",
        "completed_at",
        "abandoned_at",
        "challenges_attempted",
        "device_type",
        "distraction_free",
    ]
    rows = _build_rows(
        sessions,
        lambda s: [
            s.pk,
            _anon_id(s.participant_id),
            s.status,
            _date_only(s.started_at),
            _date_only(s.completed_at),
            _date_only(s.abandoned_at),
            s.challenges_attempted,
            s.device_type,
            s.distraction_free,
        ],
    )

    count = _write_csv(output_dir / "code_sessions.csv", headers, rows)
    _write_parquet(
        output_dir / "code_sessions.parquet",
        headers,
        rows,
    )
    return count


def export_code_session_challenges(output_dir):
    """Export code session challenge assignments."""
    from agenticbrainrot.coding_sessions.models import CodeSessionChallenge  # noqa: PLC0415

    records = CodeSessionChallenge.objects.filter(
        session__participant__withdrawn_at__isnull=True,
        session__participant__user__is_staff=False,
        session__participant__user__is_superuser=False,
    ).select_related("session__participant")

    headers = [
        "session_id",
        "challenge_id",
        "position",
        "assigned_at",
    ]
    rows = _build_rows(
        records,
        lambda r: [
            r.session_id,
            r.challenge_id,
            r.position,
            _date_only(r.assigned_at),
        ],
    )

    count = _write_csv(
        output_dir / "code_session_challenges.csv",
        headers,
        rows,
    )
    _write_parquet(
        output_dir / "code_session_challenges.parquet",
        headers,
        rows,
    )
    return count


def export_challenge_attempts(output_dir):
    """Export challenge attempt data (without submitted code)."""
    from agenticbrainrot.challenges.models import ChallengeAttempt  # noqa: PLC0415

    attempts = ChallengeAttempt.objects.filter(
        participant__withdrawn_at__isnull=True,
        participant__user__is_staff=False,
        participant__user__is_superuser=False,
    ).select_related("participant")

    headers = [
        "participant_id",
        "challenge_id",
        "session_id",
        "tests_passed",
        "tests_total",
        "time_taken_seconds",
        "active_time_seconds",
        "idle_time_seconds",
        "started_at",
        "submitted_at",
        "skipped",
        "paste_count",
        "paste_total_chars",
        "keystroke_count",
        "tab_blur_count",
    ]
    rows = _build_rows(
        attempts,
        lambda a: [
            _anon_id(a.participant_id),
            a.challenge_id,
            a.session_id,
            a.tests_passed,
            a.tests_total,
            a.time_taken_seconds,
            a.active_time_seconds,
            a.idle_time_seconds,
            _date_only(a.started_at),
            _date_only(a.submitted_at),
            a.skipped,
            a.paste_count,
            a.paste_total_chars,
            a.keystroke_count,
            a.tab_blur_count,
        ],
    )

    count = _write_csv(
        output_dir / "challenge_attempts.csv",
        headers,
        rows,
    )
    _write_parquet(
        output_dir / "challenge_attempts.parquet",
        headers,
        rows,
    )
    return count


def export_challenges(output_dir):
    """Export challenge metadata."""
    from agenticbrainrot.challenges.models import Challenge  # noqa: PLC0415

    challenges = Challenge.objects.all()

    headers = [
        "challenge_id",
        "external_id",
        "title",
        "difficulty",
        "tags",
        "is_active",
        "created_at",
    ]
    rows = _build_rows(
        challenges,
        lambda c: [
            c.pk,
            c.external_id,
            c.title,
            c.difficulty,
            json.dumps(c.tags),
            c.is_active,
            _date_only(c.created_at),
        ],
    )

    count = _write_csv(output_dir / "challenges.csv", headers, rows)
    _write_parquet(output_dir / "challenges.parquet", headers, rows)
    return count


def export_survey_questions(output_dir):
    """Export survey question metadata."""
    from agenticbrainrot.surveys.models import SurveyQuestion  # noqa: PLC0415

    questions = SurveyQuestion.objects.all()

    headers = [
        "question_id",
        "text",
        "question_type",
        "context",
        "category",
        "is_required",
        "is_active",
        "display_order",
    ]
    rows = _build_rows(
        questions,
        lambda q: [
            q.pk,
            q.text,
            q.question_type,
            q.context,
            q.category,
            q.is_required,
            q.is_active,
            q.display_order,
        ],
    )

    count = _write_csv(
        output_dir / "survey_questions.csv",
        headers,
        rows,
    )
    _write_parquet(
        output_dir / "survey_questions.parquet",
        headers,
        rows,
    )
    return count


def export_survey_responses(output_dir):
    """Export survey responses with opaque participant IDs."""
    from agenticbrainrot.surveys.models import SurveyResponse  # noqa: PLC0415

    responses = SurveyResponse.objects.filter(
        participant__withdrawn_at__isnull=True,
        participant__user__is_staff=False,
        participant__user__is_superuser=False,
    ).select_related("participant")

    headers = [
        "participant_id",
        "question_id",
        "value",
        "answered_at",
        "session_id",
        "challenge_attempt_id",
    ]
    rows = _build_rows(
        responses,
        lambda r: [
            _anon_id(r.participant_id),
            r.question_id,
            r.value,
            _date_only(r.answered_at),
            r.session_id or "",
            r.challenge_attempt_id or "",
        ],
    )

    count = _write_csv(
        output_dir / "survey_responses.csv",
        headers,
        rows,
    )
    _write_parquet(
        output_dir / "survey_responses.parquet",
        headers,
        rows,
    )
    return count


# Codebook definitions  -  each tuple: (file, column, type, description, allowed_values)
CODEBOOK = [
    (
        "participants.csv",
        "participant_id",
        "string",
        "HMAC-anonymised participant ID",
        "",
    ),
    (
        "participants.csv",
        "has_active_consent",
        "boolean",
        "Active consent",
        "True/False",
    ),
    (
        "participants.csv",
        "profile_completed",
        "boolean",
        "Profile intake completed",
        "True/False",
    ),
    (
        "participants.csv",
        "profile_updated_at",
        "date",
        "Profile last updated",
        "YYYY-MM-DD",
    ),
    ("code_sessions.csv", "session_id", "integer", "Session primary key", ""),
    (
        "code_sessions.csv",
        "participant_id",
        "string",
        "HMAC-anonymised participant ID",
        "",
    ),
    (
        "code_sessions.csv",
        "status",
        "string",
        "Session status",
        "in_progress/completed/abandoned",
    ),
    ("code_sessions.csv", "started_at", "date", "Session start date", "YYYY-MM-DD"),
    ("code_sessions.csv", "completed_at", "date", "Completion date", "YYYY-MM-DD"),
    ("code_sessions.csv", "abandoned_at", "date", "Abandonment date", "YYYY-MM-DD"),
    (
        "code_sessions.csv",
        "challenges_attempted",
        "integer",
        "Challenges attempted",
        "",
    ),
    (
        "code_sessions.csv",
        "device_type",
        "string",
        "Device type",
        "desktop/laptop/tablet/phone",
    ),
    (
        "code_sessions.csv",
        "distraction_free",
        "string",
        "Distraction-free",
        "yes/mostly/no",
    ),
    ("code_session_challenges.csv", "session_id", "integer", "Session PK", ""),
    ("code_session_challenges.csv", "challenge_id", "integer", "Challenge PK", ""),
    ("code_session_challenges.csv", "position", "integer", "Position in session", ""),
    (
        "code_session_challenges.csv",
        "assigned_at",
        "date",
        "Assignment date",
        "YYYY-MM-DD",
    ),
    ("challenge_attempts.csv", "participant_id", "string", "HMAC-anonymised ID", ""),
    ("challenge_attempts.csv", "challenge_id", "integer", "Challenge PK", ""),
    ("challenge_attempts.csv", "session_id", "integer", "Session PK", ""),
    ("challenge_attempts.csv", "tests_passed", "integer", "Tests passed", ""),
    ("challenge_attempts.csv", "tests_total", "integer", "Total tests", ""),
    ("challenge_attempts.csv", "time_taken_seconds", "float", "Time taken (s)", ""),
    ("challenge_attempts.csv", "active_time_seconds", "float", "Active time (s)", ""),
    ("challenge_attempts.csv", "idle_time_seconds", "float", "Idle time (s)", ""),
    ("challenge_attempts.csv", "started_at", "date", "Start date", "YYYY-MM-DD"),
    ("challenge_attempts.csv", "submitted_at", "date", "Submission date", "YYYY-MM-DD"),
    ("challenge_attempts.csv", "skipped", "boolean", "Skipped", "True/False"),
    ("challenge_attempts.csv", "paste_count", "integer", "Paste events", ""),
    ("challenge_attempts.csv", "paste_total_chars", "integer", "Pasted chars", ""),
    ("challenge_attempts.csv", "keystroke_count", "integer", "Keystrokes", ""),
    ("challenge_attempts.csv", "tab_blur_count", "integer", "Tab blur events", ""),
    ("challenges.csv", "challenge_id", "integer", "Challenge PK", ""),
    ("challenges.csv", "external_id", "string", "Versioned external ID", ""),
    ("challenges.csv", "title", "string", "Challenge title", ""),
    ("challenges.csv", "difficulty", "integer", "Difficulty tier", "1-5"),
    ("challenges.csv", "tags", "json", "Challenge tags", ""),
    ("challenges.csv", "is_active", "boolean", "Active", "True/False"),
    ("challenges.csv", "created_at", "date", "Creation date", "YYYY-MM-DD"),
    ("survey_questions.csv", "question_id", "integer", "Question PK", ""),
    ("survey_questions.csv", "text", "string", "Question text", ""),
    (
        "survey_questions.csv",
        "question_type",
        "string",
        "Type",
        "text/number/single_choice/multi_choice/scale",
    ),
    (
        "survey_questions.csv",
        "context",
        "string",
        "Context",
        "profile/post_challenge/post_session",
    ),
    ("survey_questions.csv", "category", "string", "Category", ""),
    ("survey_questions.csv", "is_required", "boolean", "Required", "True/False"),
    ("survey_questions.csv", "is_active", "boolean", "Active", "True/False"),
    ("survey_questions.csv", "display_order", "integer", "Display order", ""),
    ("survey_responses.csv", "participant_id", "string", "HMAC-anonymised ID", ""),
    ("survey_responses.csv", "question_id", "integer", "Question PK", ""),
    ("survey_responses.csv", "value", "string", "Response value", ""),
    ("survey_responses.csv", "answered_at", "date", "Response date", "YYYY-MM-DD"),
    ("survey_responses.csv", "session_id", "integer", "Session FK", ""),
    ("survey_responses.csv", "challenge_attempt_id", "integer", "Attempt FK", ""),
]


def write_codebook(output_dir):
    """Write codebook.csv describing all exported columns."""
    headers = [
        "file",
        "column",
        "data_type",
        "description",
        "allowed_values",
    ]
    _write_csv(output_dir / "codebook.csv", headers, CODEBOOK)


def write_manifest(output_dir, version_slug, row_counts):
    """Write manifest.json with metadata about the export."""
    checksums = {}
    for f in sorted(output_dir.iterdir()):
        if f.name in ("manifest.json", "codebook.csv"):
            continue
        checksums[f.name] = _sha256_file(f)

    manifest = {
        "version": version_slug,
        "exported_at": timezone.now().isoformat(),
        "git_commit": _git_hash(),
        "row_counts": row_counts,
        "checksums": checksums,
    }

    with (output_dir / "manifest.json").open("w") as f:
        json.dump(manifest, f, indent=2)

    return manifest


def run_export(output_dir=None):
    """Run the full dataset export pipeline."""
    today = timezone.now().date()
    version_slug = f"v{today.isoformat()}"

    output_dir = Path("exports") / version_slug if output_dir is None else Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    row_counts = {
        "participants": export_participants(output_dir),
        "code_sessions": export_code_sessions(output_dir),
        "code_session_challenges": export_code_session_challenges(
            output_dir,
        ),
        "challenge_attempts": export_challenge_attempts(output_dir),
        "challenges": export_challenges(output_dir),
        "survey_questions": export_survey_questions(output_dir),
        "survey_responses": export_survey_responses(output_dir),
    }

    write_codebook(output_dir)
    manifest = write_manifest(output_dir, version_slug, row_counts)

    log_audit_event(
        "dataset_export_run",
        actor=None,
        version=version_slug,
        row_counts=row_counts,
    )

    return output_dir, manifest
