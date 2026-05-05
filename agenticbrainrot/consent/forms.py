from django import forms


class ConsentForm(forms.Form):
    """Form for giving consent."""

    consent = forms.BooleanField(
        required=True,
        label=("I have read and understand the above, and I consent to participate"),
    )
