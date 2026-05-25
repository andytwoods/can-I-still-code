"""
Reproduce all reported statistics for the 2026-05-24 AI usage analysis.

Reads data.json from the same directory (or fetches it from GitHub if not found).

Usage:
    python analyse.py

Requirements:
    pip install scipy
"""

import json
import urllib.request
from pathlib import Path

import numpy as np
from scipy import stats

DATA_URL = (
    "https://raw.githubusercontent.com/andytwoods/can-I-still-code"
    "/master/analysis/2026-05-24-ai-usage-correlation/data.json"
)


def load_data():
    local = Path(__file__).parent / "data.json"
    if local.exists():
        return json.loads(local.read_text())
    print(f"data.json not found locally – fetching from {DATA_URL}")
    with urllib.request.urlopen(DATA_URL) as r:
        return json.loads(r.read())


def pearson(xs, ys):
    if len(xs) < 2:
        return None, None, None, None
    r, p = stats.pearsonr(xs, ys)
    ci = stats.pearsonr(xs, ys).confidence_interval(confidence_level=0.95)
    return round(r, 3), round(p, 3), round(ci.low, 2), round(ci.high, 2)


def corr_pairs(sessions, field):
    pairs = [(s["ai_pct"], s[field]) for s in sessions if s.get(field) is not None]
    if not pairs:
        return None, None, None, None, 0
    xs, ys = zip(*pairs)
    r, p, lo, hi = pearson(list(xs), list(ys))
    return r, p, lo, hi, len(pairs)


def group_stats(sessions, pred):
    sub = [s for s in sessions if pred(s["ai_pct"])]
    if not sub:
        return {}
    def avg(field):
        vals = [s[field] for s in sub if s.get(field) is not None]
        return round(float(np.mean(vals)), 1) if vals else None
    return {
        "n": len(sub),
        "avg_accuracy": avg("avg_accuracy"),
        "avg_completion_rate": avg("completion_rate"),
        "avg_time_s": avg("avg_time_s"),
        "avg_efficiency_ratio": avg("avg_efficiency_ratio"),
    }


def main():
    data = load_data()
    sessions = data["sessions"]
    participants = data.get("participants", [])

    print(f"\n=== AI Usage Analysis — {data['generated_at']} ===")
    print(f"Sessions: {data['n_sessions']}  excluded: {data['n_sessions_excluded']}")

    # ── Session-level correlations ────────────────────────────────────────────
    print("\n── Session-level correlations (AI usage % vs outcome) ──")
    fields = [
        ("avg_accuracy",         "Accuracy"),
        ("completion_rate",      "Completion rate"),
        ("avg_time_s",           "Active time/challenge"),
        ("avg_efficiency_ratio", "Efficiency ratio"),
    ]
    for field, label in fields:
        r, p, lo, hi, n = corr_pairs(sessions, field)
        print(f"  {label:<22} r={r:>6}  p={p:.3f}  n={n}  95% CI [{lo}, {hi}]")

    # ── Group breakdown ───────────────────────────────────────────────────────
    print("\n── Performance by AI usage group ──")
    groups = [
        ("Low  (≤25%)",   lambda x: x <= 25),
        ("Mid  (26–75%)", lambda x: 26 <= x <= 75),
        ("High (>75%)",   lambda x: x > 75),
    ]
    for label, pred in groups:
        g = group_stats(sessions, pred)
        print(f"  {label}  n={g['n']}  acc={g['avg_accuracy']}%  "
              f"completion={g['avg_completion_rate']}%  "
              f"time={g['avg_time_s']}s  efficiency={g['avg_efficiency_ratio']}")

    # ── Efficiency outlier sensitivity ────────────────────────────────────────
    eff_pairs = [(s["ai_pct"], s["avg_efficiency_ratio"])
                 for s in sessions if s.get("avg_efficiency_ratio") is not None]
    if eff_pairs:
        outlier = max(eff_pairs, key=lambda p: p[1])
        pairs_no_out = [p for p in eff_pairs if p != outlier]
        xs, ys = zip(*pairs_no_out)
        r_no_out, p_no_out, _, _ = pearson(list(xs), list(ys))
        print(f"\n── Efficiency outlier sensitivity ──")
        print(f"  Outlier: ai_pct={outlier[0]}%  efficiency_ratio={outlier[1]}")
        r_all, _, _, _, _ = corr_pairs(sessions, "avg_efficiency_ratio")
        print(f"  r with outlier:    {r_all}")
        print(f"  r without outlier: {r_no_out}  p={p_no_out}  (n={len(pairs_no_out)})")

    # ── Participant-level: experience vs AI usage ─────────────────────────────
    if participants:
        print(f"\n── Experience vs AI usage (participant-level, n={len(participants)}) ──")
        prog = [(p["ai_pct"], p["prog_years"])   for p in participants if p.get("prog_years")   is not None]
        pyth = [(p["ai_pct"], p["python_years"]) for p in participants if p.get("python_years") is not None]

        for label, pairs in [("Prog years  vs AI%", prog), ("Python years vs AI%", pyth)]:
            xs, ys = zip(*pairs)
            r, p, lo, hi = pearson(list(xs), list(ys))
            print(f"  {label}  r={r}  p={p:.3f}  n={len(pairs)}  95% CI [{lo}, {hi}]")
    else:
        print("\n(No participant-level data in this data.json – experience correlations unavailable)")


if __name__ == "__main__":
    main()
