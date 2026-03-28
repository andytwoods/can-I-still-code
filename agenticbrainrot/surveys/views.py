import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from agenticbrainrot.accounts.models import log_audit_event

from .forms import build_survey_form
from .models import SurveyQuestion
from .models import SurveyResponse


def _get_categories(context="profile"):
    """Return ordered list of distinct categories for the given context."""
    from django.db.models import Min  # noqa: PLC0415

    return list(
        SurveyQuestion.objects.filter(
            context=context,
            is_active=True,
        )
        .values("category")
        .annotate(min_order=Min("display_order"))
        .order_by("min_order")
        .values_list("category", flat=True),
    )


def _get_questions_for_category(category, context="profile"):
    return SurveyQuestion.objects.filter(
        context=context,
        category=category,
        is_active=True,
    ).order_by("display_order")


def _prefill_form(form_class, participant, questions_qs):
    """Pre-fill a form with existing responses (latest non-superseded)."""
    initial = {}
    for q in questions_qs:
        response = (
            SurveyResponse.objects.filter(
                participant=participant,
                question=q,
                supersedes__isnull=True,
            )
            .exclude(
                superseded_by__isnull=False,
            )
            .order_by("-answered_at")
            .first()
        )
        if response:
            field_name = f"question_{q.pk}"
            if q.question_type == "multi_choice":
                initial[field_name] = json.loads(response.value)
            elif q.question_type in ("number", "scale"):
                initial[field_name] = int(response.value) if response.value else None
            else:
                initial[field_name] = response.value
    return form_class(initial=initial)


def _save_responses(form, participant, questions_qs):
    """Save form responses, superseding old ones if they exist."""
    for q in questions_qs:
        field_name = f"question_{q.pk}"
        raw_value = form.cleaned_data.get(field_name)
        if raw_value is None or raw_value in ("", []):
            continue

        value = json.dumps(raw_value) if isinstance(raw_value, list) else str(raw_value)

        # Find the latest current response to supersede
        old_response = (
            SurveyResponse.objects.filter(
                participant=participant,
                question=q,
            )
            .exclude(superseded_by__isnull=False)
            .order_by("-answered_at")
            .first()
        )

        SurveyResponse.objects.create(
            participant=participant,
            question=q,
            value=value,
            supersedes=old_response,
        )


@login_required
def profile_intake(request):
    """
    Multi-step HTMX profile intake view.

    Same-endpoint pattern: detects HX-Request header and returns
    partials for category steps.
    """
    participant = request.user.participant
    categories = _get_categories("profile")

    if not categories:
        return render(request, "surveys/no_questions.html")

    is_htmx = request.headers.get("HX-Request") == "true"

    # Determine current step from POST data or query param
    step = int(request.POST.get("step", request.GET.get("step", 0)))
    step = max(0, min(step, len(categories) - 1))

    current_category = categories[step]
    questions = _get_questions_for_category(current_category)
    form_class = build_survey_form(questions)

    if request.method == "POST" and is_htmx:
        form = form_class(request.POST)
        if form.is_valid():
            _save_responses(form, participant, questions)

            # Move to next step or finish
            next_step = step + 1
            if next_step >= len(categories):
                # All categories complete
                participant.profile_completed = True
                participant.profile_updated_at = timezone.now()
                participant.save(
                    update_fields=["profile_completed", "profile_updated_at"],
                )
                log_audit_event(
                    "profile_completed",
                    participant=participant,
                    actor=request.user,
                )
                response = HttpResponse()
                response["HX-Redirect"] = "/"
                return response

            # Render next category
            next_category = categories[next_step]
            next_questions = _get_questions_for_category(next_category)
            next_form_class = build_survey_form(next_questions)
            next_form = _prefill_form(
                next_form_class,
                participant,
                next_questions,
            )

            return render(
                request,
                "surveys/partials/_intake_step.html",
                {
                    "form": next_form,
                    "step": next_step,
                    "total_steps": len(categories),
                    "category": next_category,
                },
            )

        # Validation errors  -  re-render current step
        return render(
            request,
            "surveys/partials/_intake_step.html",
            {
                "form": form,
                "step": step,
                "total_steps": len(categories),
                "category": current_category,
            },
        )

    # GET request  -  render full page with first (or requested) step
    form = _prefill_form(form_class, participant, questions)

    if is_htmx:
        return render(
            request,
            "surveys/partials/_intake_step.html",
            {
                "form": form,
                "step": step,
                "total_steps": len(categories),
                "category": current_category,
            },
        )

    return render(
        request,
        "surveys/profile_intake.html",
        {
            "form": form,
            "step": step,
            "total_steps": len(categories),
            "category": current_category,
            "categories": categories,
        },
    )
