"""
Management command to (re)generate analysis/2026-05-24-ai-usage-correlation/data.json.

Run with:
    DJANGO_READ_DOT_ENV_FILE=True python manage.py analyse_ai_usage \
        --settings=config.settings.remote_on_local
"""

import json
import math
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db.models import Avg, Count, F, Q

from agenticbrainrot.challenges.models import ChallengeAttempt
from agenticbrainrot.coding_sessions.models import CodeSession
from agenticbrainrot.surveys.models import SurveyResponse

ANALYSIS_DIR = (
    Path(__file__).resolve().parents[4] / "analysis" / "2026-05-24-ai-usage-correlation"
)

POST_SESSION_Q = 43
PROFILE_FALLBACK_Q = 46


def _pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return None
    return round(num / (dx * dy), 3)


class Command(BaseCommand):
    help = "Regenerate data.json for the 2026-05-24 AI usage correlation analysis."

    def add_arguments(self, parser):
        parser.add_argument(
            "--date",
            default="2026-05-24",
            help="Generation date tag written into data.json (default: today).",
        )

    def handle(self, *args, **options):
        date_tag = options["date"]

        # AI usage per session (post-session survey)
        session_ai_pct = {}
        for r in SurveyResponse.objects.filter(question_id=POST_SESSION_Q):
            try:
                session_ai_pct[r.session_id] = float(r.value)
            except (ValueError, TypeError):
                pass

        # AI usage per participant (profile fallback)
        ai_pct_by_participant = {}
        for r in SurveyResponse.objects.filter(question_id=PROFILE_FALLBACK_Q).order_by("answered_at"):
            try:
                ai_pct_by_participant[r.participant_id] = float(r.value)
            except (ValueError, TypeError):
                pass

        sessions_data = []
        excluded = 0

        for sess in CodeSession.objects.filter(
            is_mock=False,
            status="completed",
            participant__user__is_staff=False,
            participant__user__is_superuser=False,
        ).order_by("id"):
            ai = session_ai_pct.get(sess.id) or ai_pct_by_participant.get(sess.participant_id)
            if ai is None:
                excluded += 1
                continue

            attempts = ChallengeAttempt.objects.filter(
                session=sess, skipped=False, tests_total__gt=0
            )
            agg = attempts.aggregate(
                avg_acc=Avg(F("tests_passed") * 100.0 / F("tests_total")),
                avg_time=Avg("time_taken_seconds"),
                n=Count("id"),
                passed=Count("id", filter=Q(tests_passed=F("tests_total"))),
                avg_efficiency=Avg("efficiency_ratio"),
            )

            if agg["n"] == 0:
                excluded += 1
                continue

            n = agg["n"]
            completion_rate = round(agg["passed"] / n * 100, 1) if n else None
            efficiency_n = attempts.filter(efficiency_ratio__isnull=False).count()

            sessions_data.append({
                "ai_pct": ai,
                "ai_source": "post_session" if sess.id in session_ai_pct else "profile",
                "avg_accuracy": round(agg["avg_acc"], 1) if agg["avg_acc"] is not None else None,
                "avg_time_s": round(agg["avg_time"], 1) if agg["avg_time"] is not None else None,
                "completion_rate": completion_rate,
                "n_attempts": n,
                "avg_efficiency_ratio": round(agg["avg_efficiency"], 3) if agg["avg_efficiency"] is not None else None,
                "efficiency_n": efficiency_n,
            })

        for i, s in enumerate(sessions_data, start=1):
            s["row"] = i

        # Correlations
        def corr_pairs(field):
            pairs = [(s["ai_pct"], s[field]) for s in sessions_data if s[field] is not None]
            return _pearson([p[0] for p in pairs], [p[1] for p in pairs]), len(pairs)

        r_acc, n_acc = corr_pairs("avg_accuracy")
        r_comp, n_comp = corr_pairs("completion_rate")
        r_speed, n_speed = corr_pairs("avg_time_s")
        r_eff, n_eff = corr_pairs("avg_efficiency_ratio")

        # Group breakdown
        def group_stats(pred):
            subset = [s for s in sessions_data if pred(s["ai_pct"])]
            if not subset:
                return {}
            return {
                "n": len(subset),
                "avg_accuracy": round(sum(s["avg_accuracy"] for s in subset if s["avg_accuracy"] is not None) / len(subset), 1),
                "avg_completion_rate": round(sum(s["completion_rate"] for s in subset if s["completion_rate"] is not None) / len(subset), 1),
                "avg_time_s": round(sum(s["avg_time_s"] for s in subset if s["avg_time_s"] is not None) / len(subset), 1),
                "avg_efficiency_ratio": (
                    round(sum(s["avg_efficiency_ratio"] for s in subset if s["avg_efficiency_ratio"] is not None) /
                          max(1, sum(1 for s in subset if s["avg_efficiency_ratio"] is not None)), 3)
                    if any(s["avg_efficiency_ratio"] is not None for s in subset) else None
                ),
            }

        data = {
            "generated_at": date_tag,
            "source": "production DB via config.settings.remote_on_local",
            "n_sessions": len(sessions_data),
            "n_sessions_excluded": excluded,
            "ai_usage_questions": {
                "post_session_id": POST_SESSION_Q,
                "profile_fallback_id": PROFILE_FALLBACK_Q,
            },
            "correlations": {
                "ai_pct_vs_accuracy_r": r_acc,
                "ai_pct_vs_accuracy_n": n_acc,
                "ai_pct_vs_completion_rate_r": r_comp,
                "ai_pct_vs_completion_rate_n": n_comp,
                "ai_pct_vs_speed_r": r_speed,
                "ai_pct_vs_speed_n": n_speed,
                "ai_pct_vs_efficiency_ratio_r": r_eff,
                "ai_pct_vs_efficiency_ratio_n": n_eff,
            },
            "groups": {
                "low_lte25": group_stats(lambda x: x <= 25),
                "mid_26_75": group_stats(lambda x: 26 <= x <= 75),
                "high_gt75": group_stats(lambda x: x > 75),
            },
            "sessions": sessions_data,
        }

        out_path = ANALYSIS_DIR / "data.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(data, indent=2))

        self.stdout.write(self.style.SUCCESS(f"Written: {out_path}"))
        self.stdout.write(f"\nSessions included: {len(sessions_data)}  excluded: {excluded}")
        self.stdout.write(f"\nCorrelations:")
        self.stdout.write(f"  Accuracy        r={r_acc}  (n={n_acc})")
        self.stdout.write(f"  Completion rate r={r_comp}  (n={n_comp})")
        self.stdout.write(f"  Speed           r={r_speed}  (n={n_speed})")
        self.stdout.write(f"  Efficiency ratio r={r_eff}  (n={n_eff})")

        # Coverage summary for efficiency
        total_attempts = sum(s["n_attempts"] for s in sessions_data)
        eff_attempts = sum(s["efficiency_n"] for s in sessions_data)
        self.stdout.write(
            f"\nEfficiency coverage: {eff_attempts}/{total_attempts} attempts "
            f"({round(eff_attempts/total_attempts*100) if total_attempts else 0}%)"
        )
