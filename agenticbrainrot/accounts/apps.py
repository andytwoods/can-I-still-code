from django.apps import AppConfig
from django.core.checks import Error
from django.core.checks import register


class AccountsConfig(AppConfig):
    name = "agenticbrainrot.accounts"
    verbose_name = "Accounts"

    def ready(self):
        from django.db.models.signals import post_save  # noqa: PLC0415

        from agenticbrainrot.accounts.models import Participant  # noqa: PLC0415
        from agenticbrainrot.accounts.models import User  # noqa: PLC0415

        def create_participant(sender, instance, created, **kwargs):
            if created:
                Participant.objects.create(user=instance)

        post_save.connect(
            create_participant,
            sender=User,
            dispatch_uid="create_participant_on_user_create",
        )


@register()
def check_study_settings(app_configs, **kwargs):
    from django.conf import settings  # noqa: PLC0415

    errors = []
    study = getattr(settings, "STUDY", None)
    if study is None:
        errors.append(
            Error(
                "STUDY settings dict is not defined.",
                hint="Add a STUDY dict to your settings with required keys.",
                id="accounts.E001",
            ),
        )
        return errors

    # Check required keys exist
    required_keys = {
        "TIER_DISTRIBUTION",
        "CHALLENGES_PER_SESSION",
        "SESSION_COOLDOWN_DAYS",
        "SESSION_TIMEOUT_HOURS",
        "MIN_GROUP_SIZE_FOR_AGGREGATES",
    }
    missing = required_keys - set(study.keys())
    if missing:
        errors.append(
            Error(
                f"STUDY settings dict is missing keys: {missing}",
                hint="Ensure all required keys are present in the STUDY dict.",
                id="accounts.E002",
            ),
        )
        return errors

    # Validate TIER_DISTRIBUTION
    tier_dist = study["TIER_DISTRIBUTION"]
    expected_keys = {"1", "2", "3", "4", "5"}
    if set(tier_dist.keys()) != expected_keys:
        errors.append(
            Error(
                f"STUDY['TIER_DISTRIBUTION'] keys must be {expected_keys}, "
                f"got {set(tier_dist.keys())}.",
                id="accounts.E003",
            ),
        )
    elif not all(isinstance(v, int) and v >= 0 for v in tier_dist.values()):
        errors.append(
            Error(
                "STUDY['TIER_DISTRIBUTION'] values must be non-negative integers.",
                id="accounts.E004",
            ),
        )
    elif sum(tier_dist.values()) != study["CHALLENGES_PER_SESSION"]:
        errors.append(
            Error(
                f"STUDY['TIER_DISTRIBUTION'] values must sum to "
                f"CHALLENGES_PER_SESSION ({study['CHALLENGES_PER_SESSION']}), "
                f"got {sum(tier_dist.values())}.",
                id="accounts.E005",
            ),
        )

    # Validate cooldown and timeout
    if study["SESSION_COOLDOWN_DAYS"] < 1:
        errors.append(
            Error(
                "STUDY['SESSION_COOLDOWN_DAYS'] must be >= 1.",
                id="accounts.E006",
            ),
        )
    if study["SESSION_TIMEOUT_HOURS"] < 1:
        errors.append(
            Error(
                "STUDY['SESSION_TIMEOUT_HOURS'] must be >= 1.",
                id="accounts.E007",
            ),
        )

    return errors
