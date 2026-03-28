from django import forms

from .models import CodeSession


class SessionStartForm(forms.Form):
    """Form for starting a new coding session."""

    device_type = forms.ChoiceField(
        choices=CodeSession.DeviceType.choices,
        widget=forms.RadioSelect,
        label="What device are you using?",
    )
    acknowledge = forms.BooleanField(
        label=("I acknowledge that I will work independently, without external help or AI tools, during this session."),
        required=True,
    )


class MockSessionStartForm(forms.Form):
    """Simplified form for staff mock sessions (no acknowledgement needed)."""

    device_type = forms.ChoiceField(
        choices=CodeSession.DeviceType.choices,
        widget=forms.RadioSelect,
        label="What device are you using?",
    )
