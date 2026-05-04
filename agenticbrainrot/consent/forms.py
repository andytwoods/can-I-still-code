from django import forms

from .models import OptionalConsentRecord


class ConsentForm(forms.Form):
    """Form for giving consent and optional consent choices."""

    consent = forms.BooleanField(
        required=True,
        label=("I have read and understand the above, and I consent to participate"),
    )


