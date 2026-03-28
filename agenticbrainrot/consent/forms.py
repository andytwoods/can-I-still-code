from django import forms

from .models import OptionalConsentRecord


class ConsentForm(forms.Form):
    """Form for giving consent and optional consent choices."""

    consent = forms.BooleanField(
        required=True,
        label=(
            "I have read and understand the above, "
            "and I consent to participate"
        ),
    )

    # Optional consent checkboxes
    reminder_emails = forms.BooleanField(
        required=False,
        label="I agree to receive reminder emails about upcoming sessions",
    )
    think_aloud_audio = forms.BooleanField(
        required=False,
        label="I agree to optional think-aloud audio recording",
    )
    transcript_sharing = forms.BooleanField(
        required=False,
        label="I agree to share my anonymised transcripts for research",
    )
    future_contact = forms.BooleanField(
        required=False,
        label="I agree to be contacted for a follow-up interview",
    )

    OPTIONAL_CONSENT_FIELDS = {
        "reminder_emails": OptionalConsentRecord.ConsentType.REMINDER_EMAILS,
        "think_aloud_audio": OptionalConsentRecord.ConsentType.THINK_ALOUD_AUDIO,
        "transcript_sharing": OptionalConsentRecord.ConsentType.TRANSCRIPT_SHARING,
        "future_contact": OptionalConsentRecord.ConsentType.FUTURE_CONTACT,
    }
