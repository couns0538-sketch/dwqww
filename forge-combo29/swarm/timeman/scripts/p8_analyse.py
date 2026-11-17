#!/usr/bin/env python3
"""P8: analyse the accumulating-clock game runs.

Reports, per time control:
  * games, plies, forfeits, hangs, illegal moves, and how each game ended
  * the distribution of per-move engine time AGAINST the planner's prediction:
      - plan soft and plan hard for the exact clock/increment given
      - the ratio charged/hard and charged/soft
      - the count and size of any move whose time exceeded its hard plan
  * whether the planner formula reproduces every move (the +2.1 ms claim was
    made on one control; this checks the others)
  * utilisation (charged / clock before the move)

The per-move comparison uses the ENGINE's own reported time (`time <ms>` on the
last info line), because that is what the clock is charged in p3_games.py.
Harness wall time is reported separately as `tail_ms` so the two are never
conflated.
"""
from __future__ import annotations

import json
import os
import statistics
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucilib import plan_clock  # noqa: E402

OVH = 10


def pct(vals, q):
    if not vals:
        return None
    s = sorted(vals)
    k = (len(s) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def main():
    path = sys.argv[1]
    outdir = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(path)
    d = json.load(open(path))
    games = d["games"]

    by_tc = defaultdict(list)
    for g in games:
        by_tc[g["tc"]].append(g)

    summary = {}
    print(f"{'tc':>12} {'games':>6} {'plies':>7} {'forfeits':>9} {'hangs':>6} {'illegal':>8} "
          f"{'overhard':>9} {'maxover':>8}")
    for tc in sorted(by_tc, key=lambda t: int(t.split("+")[0])):
        gs = by_tc[tc]
        moves = [m for g in gs for m in g["moves"]]
        ends = Counter(g["end"].split(":")[0] for g in gs)
        forfeits = [g for g in gs if g["forfeit_by"] is not None]
        charged = [m["charged_ms"] for m in moves]
        tails = [m["tail_ms"] for m in moves]
        ratios_hard = [m["charged_ms"] / m["plan_hard"] for m in moves if m["plan_hard"]]
        ratios_soft = [m["charged_ms"] / m["plan_soft"] for m in moves if m["plan_soft"]]
        over = [m for m in moves if m["plan_hard"] and m["charged_ms"] > m["plan_hard"]]
        over_by = [m["charged_ms"] - m["plan_hard"] for m in over]
        util = [m["charged_ms"] / m["clock_before"] for m in moves if m["clock_before"] > 0]
        # Prediction error in ms against the soft plan, the same shape as the
        # established "+2.1 ms reproduces all moves" claim.
        err_soft = [m["charged_ms"] - m["plan_soft"] for m in moves]
        # How often the plan was a pure step: charged <= hard and > 0.
        summary[tc] = {
            "games": len(gs),
            "plies": len(moves),
            "forfeits": len(forfeits),
            "hangs": ends.get("harness_hang", 0),
            "illegal": ends.get("illegal_or_null", 0),
            "ends": dict(ends),
            "clock_mapping_errors": sum(g.get("clock_mapping_errors", 0) for g in gs),
            "charged_ms": {
                "min": min(charged) if charged else None,
                "p50": pct(charged, 0.5),
                "p90": pct(charged, 0.9),
                "p99": pct(charged, 0.99),
                "max": max(charged) if charged else None,
            },
            "tail_ms": {
                "p50": pct(tails, 0.5), "p95": pct(tails, 0.95), "max": max(tails) if tails else None,
            },
            "ratio_charged_over_hard": {
                "min": min(ratios_hard) if ratios_hard else None,
                "p50": pct(ratios_hard, 0.5), "p95": pct(ratios_hard, 0.95),
                "max": max(ratios_hard) if ratios_hard else None,
            },
            "ratio_charged_over_soft": {
                "p50": pct(ratios_soft, 0.5), "p95": pct(ratios_soft, 0.95),
                "max": max(ratios_soft) if ratios_soft else None,
            },
            "over_hard_count": len(over),
            "over_hard_max_ms": max(over_by) if over_by else 0,
            "prediction_err_vs_soft": {
                "p50": pct(err_soft, 0.5), "p95": pct(err_soft, 0.95),
                "max": max(err_soft) if err_soft else None,
                "min": min(err_soft) if err_soft else None,
                "within_2ms": sum(1 for e in err_soft if abs(e) <= 2),
                "n": len(err_soft),
            },
            "utilisation": {
                "p50": pct(util, 0.5), "p95": pct(util, 0.95),
                "max": max(util) if util else None,
            },
            "final_clock": {
                "white_median": statistics.median([g["final_clock"]["white"] for g in gs]) if gs else None,
                "black_median": statistics.median([g["final_clock"]["black"] for g in gs]) if gs else None,
                "min": min(min(g["final_clock"].values()) for g in gs) if gs else None,
            },
        }
        s = summary[tc]
        print(f"{tc:>12} {s['games']:>6} {s['plies']:>7} {s['forfeits']:>9} {s['hangs']:>6} "
              f"{s['illegal']:>8} {s['over_hard_count']:>9} {s['over_hard_max_ms']:>8.1f}")

    print()
    for tc, s in summary.items():
        print(f"--- {tc} ---")
        print(f"  charged ms   min={s['charged_ms']['min']:.1f} p50={s['charged_ms']['p50']:.1f} "
              f"p90={s['charged_ms']['p90']:.1f} p99={s['charged_ms']['p99']:.1f} max={s['charged_ms']['max']:.1f}")
        print(f"  tail ms      p50={s['tail_ms']['p50']:.2f} p95={s['tail_ms']['p95']:.2f} max={s['tail_ms']['max']:.2f}")
        r = s["ratio_charged_over_hard"]
        print(f"  /hard        min={r['min']:.3f} p50={r['p50']:.3f} p95={r['p95']:.3f} max={r['max']:.3f}")
        r = s["ratio_charged_over_soft"]
        print(f"  /soft        p50={r['p50']:.3f} p95={r['p95']:.3f} max={r['max']:.3f}")
        e = s["prediction_err_vs_soft"]
        print(f"  charged-soft p50={e['p50']:+.2f}ms p95={e['p95']:+.2f}ms max={e['max']:+.2f}ms "
              f"(within 2 ms: {e['within_2ms']}/{e['n']})")
        u = s["utilisation"]
        print(f"  utilisation  p50={u['p50']:.3f} p95={u['p95']:.3f} max={u['max']:.3f}")
        print(f"  ends {s['ends']}  min final clock {s['final_clock']['min']:.1f} ms  "
              f"mapping_errors={s['clock_mapping_errors']}")

    with open(os.path.join(outdir, "p8_analysis.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print("\nwrote", os.path.join(outdir, "p8_analysis.json"))


if __name__ == "__main__":
    main()
