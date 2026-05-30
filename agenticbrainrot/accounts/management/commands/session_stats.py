from django.core.management.base import BaseCommand

from agenticbrainrot.coding_sessions.models import CodeSession


class Command(BaseCommand):
    help = "Print session counts by status"

    def handle(self, *args, **options):
        from django.db.models import Count
        total = CodeSession.objects.count()
        by_status = CodeSession.objects.values("status").annotate(n=Count("id")).order_by("-n")
        for row in by_status:
            self.stdout.write(f"  {row['status']}: {row['n']}")
        self.stdout.write(f"Total: {total}\n")

        self.stdout.write("Abandoned sessions (oldest first):")
        abandoned = CodeSession.objects.filter(status="abandoned").order_by("started_at").values(
            "id", "started_at", "abandoned_at", "participant_id"
        )
        for s in abandoned:
            started = s['started_at'].strftime('%Y-%m-%d %H:%M') if s['started_at'] else 'n/a'
            abandoned_at = s['abandoned_at'].strftime('%Y-%m-%d %H:%M') if s['abandoned_at'] else 'n/a'
            self.stdout.write(f"  id={s['id']} participant={s['participant_id']} started={started} abandoned={abandoned_at}")
