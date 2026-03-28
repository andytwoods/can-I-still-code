from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string

from allauth.account.models import EmailAddress
from allauth.account.models import EmailConfirmation

User = get_user_model()


class Command(BaseCommand):
    help = "One-shot setup: create superuser, seed challenges and survey questions."

    def handle(self, *args, **kwargs):
        self._sync_site()
        self._create_superuser()
        self._seed_challenges()
        self._seed_survey_questions()

    def _sync_site(self):
        domain = settings.DOMAIN
        Site.objects.update_or_create(
            id=settings.SITE_ID,
            defaults={"domain": domain, "name": domain},
        )
        self.stdout.write(f"Site domain set to: {domain}")

    def _create_superuser(self):
        email = "andytwoods@gmail.com"
        new_password = get_random_string(10)
        try:
            if not User.objects.filter(is_superuser=True).exists():
                self.stdout.write("No superusers found, creating one")
                user = User.objects.create_superuser(email=email, password=new_password)
                email_address = EmailAddress.objects.create(
                    user=user,
                    email=email,
                    primary=True,
                    verified=False,
                )
                EmailConfirmation.create(email_address)
                self.stdout.write("=======================")
                self.stdout.write("A superuser has been created")
                self.stdout.write(f"Email: {email}")
                self.stdout.write(f"Password: {new_password}")
                self.stdout.write("=======================")
            else:
                self.stdout.write("A superuser exists in the database. Skipping.")
        except Exception as e:
            self.stderr.write(f"There was an error creating superuser: {e}")

    def _seed_challenges(self):
        self.stdout.write("Seeding challenges...")
        try:
            call_command("seed_challenges", stdout=self.stdout, stderr=self.stderr)
        except Exception as e:
            self.stderr.write(f"There was an error seeding challenges: {e}")

    def _seed_survey_questions(self):
        self.stdout.write("Seeding survey questions...")
        try:
            call_command("seed_survey_questions", stdout=self.stdout, stderr=self.stderr)
        except Exception as e:
            self.stderr.write(f"There was an error seeding survey questions: {e}")
