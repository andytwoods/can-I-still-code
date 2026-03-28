import json
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.db import transaction
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils import timezone

from agenticbrainrot.accounts.models import Participant
from agenticbrainrot.accounts.models import log_audit_event
from agenticbrainrot.challenges.models import ChallengeAttempt
from agenticbrainrot.challenges.services import PoolExhaustedError
from agenticbrainrot.challenges.services import select_challenges_for_session
from agenticbrainrot.surveys.forms import build_survey_form
from agenticbrainrot.surveys.models import SurveyQuestion
from agenticbrainrot.surveys.models import SurveyResponse

from .forms import MockSessionStartForm
from .forms import SessionStartForm
from .models import CodeSession
from .models import CodeSessionChallenge

HTTP_CONFLICT = 409
HTTP_BAD_REQUEST = 400


def _get_participant(request):
    """Get the participant for the current user."""
    return get_object_or_404(Participant, user=request.user)


def _abandon_stale_sessions(participant):
    """Mark in_progress sessions older than SESSION_TIMEOUT_HOURS as abandoned."""
    timeout_hours = settings.STUDY["SESSION_TIMEOUT_HOURS"]
    cutoff = timezone.now() - timezone.timedelta(hours=timeout_hours)
    stale = CodeSession.objects.filter(
        participant=participant,
        status=CodeSession.Status.IN_PROGRESS,
        started_at__lt=cutoff,
    )
    for session in stale:
        session.status = CodeSession.Status.ABANDONED
        session.abandoned_at = timezone.now()
        session.save(update_fields=["status", "abandoned_at"])
        log_audit_event(
            "session_abandoned",
            participant=participant,
            actor=participant.user,
            session_id=session.pk,
        )


def _get_current_challenge(session):
    """Find the current challenge (lowest position without an attempt)."""
    session_challenges = session.session_challenges.select_related(
        "challenge",
    ).order_by("position")

    attempted_ids = set(
        session.challenge_attempts.values_list("challenge_id", flat=True),
    )

    for sc in session_challenges:
        if sc.challenge_id not in attempted_ids:
            return sc, session_challenges.count()

    return None, session_challenges.count()


def _check_28_day_rule(participant):
    """Check if 28-day cooldown has passed since last completed session."""
    cooldown_days = settings.STUDY["SESSION_COOLDOWN_DAYS"]
    last_completed = (
        CodeSession.objects.filter(
            participant=participant,
            status=CodeSession.Status.COMPLETED,
            is_mock=False,
        )
        .order_by("-completed_at")
        .first()
    )
    if last_completed and last_completed.completed_at:
        next_eligible = last_completed.completed_at + timezone.timedelta(
            days=cooldown_days,
        )
        if timezone.now() < next_eligible:
            return False, next_eligible
    return True, None


def _check_eligibility(participant):
    """Check if participant can start a session."""
    if participant.withdrawn_at:
        return "blocked", {"reason": "You have withdrawn from the study."}

    if not participant.has_active_consent:
        return "redirect_consent", None

    if not participant.profile_completed:
        return "redirect_profile", None

    return None, None


@login_required
def session_start(request):  # noqa: PLR0911
    """
    Session start page. Enforces 28-day rule, handles resumable sessions,
    and creates new sessions with challenge selection.
    """
    participant = _get_participant(request)

    # Check eligibility
    status, ctx = _check_eligibility(participant)
    if status == "blocked":
        return render(request, "coding_sessions/session_blocked.html", ctx)
    if status == "redirect_consent":
        return redirect("consent:give_consent")
    if status == "redirect_profile":
        return redirect("surveys:profile_intake")

    # Abandon stale in-progress sessions
    _abandon_stale_sessions(participant)

    # Check for resumable in-progress session
    active_session = CodeSession.objects.filter(
        participant=participant,
        status=CodeSession.Status.IN_PROGRESS,
    ).first()

    if active_session:
        return redirect(
            "coding_sessions:session_view",
            session_id=active_session.pk,
        )

    # Check 28-day rule
    eligible, next_eligible = _check_28_day_rule(participant)
    if not eligible:
        return render(
            request,
            "coding_sessions/session_blocked.html",
            {"reason": "cooldown", "next_eligible": next_eligible},
        )

    if request.method == "POST":
        form = SessionStartForm(request.POST)
        if form.is_valid():
            return _create_session(request, participant, form)
    else:
        form = SessionStartForm()

    return render(request, "coding_sessions/session_start.html", {"form": form})


def _create_session(request, participant, form):
    """Create a new session with concurrent guard."""
    try:
        with transaction.atomic():
            # Lock participant row to prevent concurrent session creation
            Participant.objects.select_for_update().get(pk=participant.pk)

            # Double-check no in-progress session exists
            if CodeSession.objects.filter(
                participant=participant,
                status=CodeSession.Status.IN_PROGRESS,
            ).exists():
                existing = CodeSession.objects.filter(
                    participant=participant,
                    status=CodeSession.Status.IN_PROGRESS,
                ).first()
                return redirect(
                    "coding_sessions:session_view",
                    session_id=existing.pk,
                )

            # Select challenges
            challenges = select_challenges_for_session(participant)

            # Create session
            session = CodeSession.objects.create(
                participant=participant,
                device_type=form.cleaned_data["device_type"],
            )

            # Create CodeSessionChallenge rows
            for i, challenge in enumerate(challenges):
                CodeSessionChallenge.objects.create(
                    session=session,
                    challenge=challenge,
                    position=i,
                )

            log_audit_event(
                "session_started",
                participant=participant,
                actor=request.user,
                session_id=session.pk,
            )

        return redirect(
            "coding_sessions:session_view",
            session_id=session.pk,
        )
    except PoolExhaustedError:
        return render(
            request,
            "coding_sessions/session_blocked.html",
            {
                "reason": "no_challenges",
            },
        )


def _handle_session_post(request, session, participant):  # noqa: PLR0911
    """Dispatch POST actions for the session view."""
    # Reject attempts on ended sessions
    if session.status in (
        CodeSession.Status.COMPLETED,
        CodeSession.Status.ABANDONED,
    ):
        return render(
            request,
            "coding_sessions/partials/_session_ended.html",
            {"session": session},
            status=HTTP_CONFLICT,
        )

    action = request.POST.get("action", "")

    if action == "submit":
        return _handle_submit(request, session, participant)
    if action == "skip":
        return _handle_skip(request, session, participant)
    if action == "stop":
        return _handle_stop(request, session, participant)
    if action == "submit_reflection":
        return _handle_reflection_submit(request, session, participant)
    if action == "skip_reflection":
        return _handle_skip_reflection(request, session, participant)
    if action == "another":
        return _render_next_challenge(request, session)
    if action == "done":
        return _render_post_session_survey(request, session)
    if action == "submit_post_session":
        return _handle_post_session_submit(request, session, participant)

    return HttpResponse("Unknown action.", status=HTTP_BAD_REQUEST)


def _render_session_get(request, session):
    """Render the session page for GET requests."""
    is_htmx = request.headers.get("HX-Request")
    current_sc, total = _get_current_challenge(session)

    if current_sc is None:
        if is_htmx:
            return _render_post_session_survey(request, session)
        return render(
            request,
            "coding_sessions/session_complete.html",
            {"session": session},
        )

    challenge = current_sc.challenge
    attempt_uuid = str(uuid.uuid4())
    context = {
        "session": session,
        "challenge": challenge,
        "position": current_sc.position + 1,
        "total_challenges": total,
        "attempt_uuid": attempt_uuid,
        "test_cases_json": json.dumps(challenge.test_cases),
    }

    if is_htmx:
        return render(
            request,
            "coding_sessions/partials/_challenge_display.html",
            context,
        )
    return render(request, "coding_sessions/challenge.html", context)


@login_required
def session_view(request, session_id):
    """
    Main session page  -  single URL for the entire session flow.
    HTMX partials swap content for challenge → reflection → another → next.
    """
    session = get_object_or_404(CodeSession, pk=session_id)
    participant = _get_participant(request)

    if session.participant != participant:
        return HttpResponseForbidden("Not your session.")

    # Abandon stale sessions
    _abandon_stale_sessions(participant)
    session.refresh_from_db()

    if request.method == "POST":
        return _handle_session_post(request, session, participant)

    return _render_session_get(request, session)


def _handle_submit(request, session, participant):
    """Handle challenge submission."""
    attempt_uuid = request.POST.get("attempt_uuid", "")

    # Idempotency check
    try:
        existing = ChallengeAttempt.objects.get(attempt_uuid=attempt_uuid)
        return _render_reflection(request, session, existing)
    except ChallengeAttempt.DoesNotExist:
        pass

    # Find current challenge
    current_sc, _ = _get_current_challenge(session)
    if current_sc is None:
        return HttpResponse("No challenge to submit.", status=HTTP_BAD_REQUEST)

    challenge = current_sc.challenge

    # Create the attempt
    attempt = ChallengeAttempt.objects.create(
        participant=participant,
        challenge=challenge,
        session=session,
        attempt_uuid=attempt_uuid,
        submitted_code=request.POST.get("submitted_code", ""),
        tests_passed=int(request.POST.get("tests_passed", 0)),
        tests_total=int(request.POST.get("tests_total", 0)),
        time_taken_seconds=float(
            request.POST.get("time_taken_seconds", 0),
        ),
        active_time_seconds=float(
            request.POST.get("active_time_seconds", 0),
        ),
        idle_time_seconds=float(
            request.POST.get("idle_time_seconds", 0),
        ),
        paste_count=int(request.POST.get("paste_count", 0)),
        paste_total_chars=int(request.POST.get("paste_total_chars", 0)),
        keystroke_count=int(request.POST.get("keystroke_count", 0)),
        tab_blur_count=int(request.POST.get("tab_blur_count", 0)),
        submitted_at=timezone.now(),
        skipped=False,
    )

    return _render_reflection(request, session, attempt)


def _handle_skip(request, session, participant):
    """Handle challenge skip."""
    current_sc, _ = _get_current_challenge(session)
    if current_sc is None:
        return HttpResponse("No challenge to skip.", status=HTTP_BAD_REQUEST)

    challenge = current_sc.challenge

    attempt = ChallengeAttempt.objects.create(
        participant=participant,
        challenge=challenge,
        session=session,
        skipped=True,
        submitted_at=timezone.now(),
    )

    return _render_reflection(request, session, attempt)


def _handle_stop(request, session, participant):
    """Handle stop session  -  skip current challenge, show post-session survey."""
    current_sc, _ = _get_current_challenge(session)
    if current_sc:
        ChallengeAttempt.objects.create(
            participant=participant,
            challenge=current_sc.challenge,
            session=session,
            skipped=True,
            submitted_at=timezone.now(),
        )

    return _render_post_session_survey(request, session)


def _render_reflection(request, session, attempt):
    """Render post-challenge reflection questions."""
    questions = SurveyQuestion.objects.filter(
        context=SurveyQuestion.Context.POST_CHALLENGE,
        is_active=True,
    ).order_by("display_order")

    form_class = build_survey_form(questions)
    form = form_class()

    return render(
        request,
        "coding_sessions/partials/_reflection.html",
        {
            "session": session,
            "attempt": attempt,
            "form": form,
            "challenge": attempt.challenge,
        },
    )


def _handle_reflection_submit(request, session, participant):
    """Save reflection responses and show another prompt."""
    attempt_id = request.POST.get("attempt_id")
    attempt = get_object_or_404(
        ChallengeAttempt,
        pk=attempt_id,
        session=session,
    )

    questions = SurveyQuestion.objects.filter(
        context=SurveyQuestion.Context.POST_CHALLENGE,
        is_active=True,
    ).order_by("display_order")

    form_class = build_survey_form(questions)
    form = form_class(request.POST)

    if form.is_valid():
        _save_survey_responses(
            participant=participant,
            questions=questions,
            form=form,
            challenge_attempt=attempt,
        )

    return _render_another_prompt(request, session)


def _handle_skip_reflection(request, session, participant):
    """Skip reflection and show another prompt."""
    return _render_another_prompt(request, session)


def _render_another_prompt(request, session):
    """Render the 'another challenge?' prompt or session complete."""
    current_sc, total = _get_current_challenge(session)
    challenges_done = session.challenge_attempts.count()

    if current_sc is None or challenges_done >= total:
        # All challenges attempted
        return _render_post_session_survey(request, session)

    return render(
        request,
        "coding_sessions/partials/_another_prompt.html",
        {
            "session": session,
            "challenges_done": challenges_done,
            "total_challenges": total,
        },
    )


def _render_next_challenge(request, session):
    """Render the next challenge partial."""
    current_sc, total = _get_current_challenge(session)
    if current_sc is None:
        return _render_post_session_survey(request, session)

    challenge = current_sc.challenge
    attempt_uuid = str(uuid.uuid4())

    return render(
        request,
        "coding_sessions/partials/_challenge_display.html",
        {
            "session": session,
            "challenge": challenge,
            "position": current_sc.position + 1,
            "total_challenges": total,
            "attempt_uuid": attempt_uuid,
            "test_cases_json": json.dumps(challenge.test_cases),
        },
    )


def _render_post_session_survey(request, session):
    """Render the post-session survey partial."""
    questions = SurveyQuestion.objects.filter(
        context=SurveyQuestion.Context.POST_SESSION,
        is_active=True,
    ).order_by("display_order")

    form_class = build_survey_form(questions)
    form = form_class()

    return render(
        request,
        "coding_sessions/partials/_post_session_survey.html",
        {
            "session": session,
            "form": form,
        },
    )


def _handle_post_session_submit(request, session, participant):
    """Save post-session survey and complete the session."""
    questions = SurveyQuestion.objects.filter(
        context=SurveyQuestion.Context.POST_SESSION,
        is_active=True,
    ).order_by("display_order")

    form_class = build_survey_form(questions)
    form = form_class(request.POST)

    if form.is_valid():
        _save_survey_responses(
            participant=participant,
            questions=questions,
            form=form,
            session=session,
        )

    # Complete the session
    session.status = CodeSession.Status.COMPLETED
    session.completed_at = timezone.now()
    session.challenges_attempted = session.challenge_attempts.count()
    session.save(
        update_fields=["status", "completed_at", "challenges_attempted"],
    )

    log_audit_event(
        "session_completed",
        participant=participant,
        actor=request.user,
        session_id=session.pk,
    )

    response = HttpResponse(status=200)
    response["HX-Redirect"] = "/results/"
    return response


def _save_survey_responses(
    participant,
    questions,
    form,
    session=None,
    challenge_attempt=None,
):
    """Save survey responses from a form."""
    for question in questions:
        field_name = f"question_{question.pk}"
        raw_value = form.cleaned_data.get(field_name)

        if raw_value is None or raw_value in ("", []):
            continue

        value = json.dumps(raw_value) if isinstance(raw_value, list) else str(raw_value)

        SurveyResponse.objects.create(
            participant=participant,
            question=question,
            value=value,
            session=session,
            challenge_attempt=challenge_attempt,
        )


def mock_session_start(request):
    """
    View to start a mock/try session that reuses the full participant
    session flow. Bypasses eligibility and cooldown checks.
    Data is flagged as mock (is_mock=True).

    Access controlled by settings.LET_PEOPLE_TRY:
      - True: open to everyone (no login required)
      - False: requires staff login
    """
    if not settings.LET_PEOPLE_TRY:
        if not request.user.is_staff:
            return redirect_to_login(request.get_full_path())
    if request.method == "POST":
        form = MockSessionStartForm(request.POST)
        if form.is_valid():
            return _create_mock_session(request, form)
    else:
        form = MockSessionStartForm()

    return render(
        request,
        "coding_sessions/mock_session_start.html",
        {"form": form},
    )


def _create_mock_session(request, form):
    """Create a mock session for the current user (or a guest)."""
    try:
        with transaction.atomic():
            user = request.user

            # For anonymous visitors when LET_PEOPLE_TRY is enabled,
            # create a temporary guest account and log them in.
            if not user.is_authenticated:
                user_model = get_user_model()
                guest_id = uuid.uuid4().hex[:12]
                user = user_model.objects.create_user(
                    email=f"guest-{guest_id}@try.agenticbrainrot.com",
                    password=None,
                    name="Guest",
                )
                login(
                    request,
                    user,
                    backend="django.contrib.auth.backends.ModelBackend",
                )

            # Get-or-create a Participant record for this user
            participant, _created = Participant.objects.get_or_create(
                user=user,
                defaults={
                    "has_active_consent": True,
                    "profile_completed": True,
                },
            )

            # Ensure consent/profile flags are set so session_view doesn't redirect
            if not participant.has_active_consent or not participant.profile_completed:
                participant.has_active_consent = True
                participant.profile_completed = True
                participant.save(
                    update_fields=["has_active_consent", "profile_completed"],
                )

            # Abandon any existing in-progress mock sessions for this user
            in_progress_mocks = CodeSession.objects.filter(
                participant=participant,
                status=CodeSession.Status.IN_PROGRESS,
                is_mock=True,
            )
            now = timezone.now()
            for session in in_progress_mocks:
                session.status = CodeSession.Status.ABANDONED
                session.abandoned_at = now
                session.save(update_fields=["status", "abandoned_at"])

            # Select challenges
            challenges = select_challenges_for_session(participant)

            # Create mock session
            session = CodeSession.objects.create(
                participant=participant,
                device_type=form.cleaned_data["device_type"],
                is_mock=True,
            )

            # Create CodeSessionChallenge rows
            for i, challenge in enumerate(challenges):
                CodeSessionChallenge.objects.create(
                    session=session,
                    challenge=challenge,
                    position=i,
                )

            log_audit_event(
                "mock_session_started",
                participant=participant,
                actor=user,
                session_id=session.pk,
            )

        return redirect(
            "coding_sessions:session_view",
            session_id=session.pk,
        )
    except PoolExhaustedError:
        return render(
            request,
            "coding_sessions/session_blocked.html",
            {"reason": "no_challenges"},
        )
