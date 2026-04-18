from captcha.fields import CaptchaField
from django import forms

WAITLIST_CONSENT_TEXT = (
    "I agree to receive a one-off email notification when the next data collection "
    "wave of the Can I Still Code study opens. I understand I can withdraw this "
    "consent at any time by clicking the unsubscribe link in that email."
)


class WaitlistSignupForm(forms.Form):
    email = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(attrs={"class": "input", "placeholder": "you@example.com"}),
    )
    consent = forms.BooleanField(
        required=True,
        label=WAITLIST_CONSENT_TEXT,
        error_messages={"required": "You must agree to receive the notification email to sign up."},
    )
    captcha = CaptchaField()
