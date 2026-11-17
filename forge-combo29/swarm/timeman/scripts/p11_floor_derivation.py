#!/usr/bin/env python3
"""P11: where the 111 ms floor comes from, as a recurrence rather than a constant.

The report records "floor 111 ms, converged from every start >= 111 at a 60 ms
increment". That is an observation. This script tests whether it falls out of the
planner, which matters because a derived floor predicts controls nobody tested
and an observed one does not.

Model, straight from include/forge/clock_plan.hpp with the engine's defaults
(TmSoftDivisor 22, TmHardPercent 60, TmHardSoftMultiple 5, Move Overhead 10):

    available = clock - 10
    soft      = available / 22
    hard      = min(available * 60/100, soft * 5)

A player that spends its whole hard limit every move moves the clock by

    clock' = clock - hard + increment

This script does NOT claim a closed form. It reports the simulation's rest
points and prints the two closed forms it tried beside them, so a miss is
visible as a miss instead of being rounded into a match.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucilib import plan_clock  # noqa: E402

OVH = 10


def simulate(start, inc, moves, spend_fraction):
    c = float(start)
    traj = [c]
    for _ in range(moves):
        _, hard, reserve = plan_clock(int(c), inc, 0, OVH)
        if reserve:
            break
        spend = min(hard * spend_fraction, c)
        c = c - spend + inc
        traj.append(c)
    return traj


def fixed_points(inc):
    """Every clock where spending the full hard limit leaves the clock unchanged."""
    out = []
    for c in range(11, 20001):
        _, hard, reserve = plan_clock(c, inc, 0, OVH)
        if reserve:
            continue
        if c - min(hard, c) + inc == c:
            out.append(c)
    return out


def main():
    outpath = sys.argv[1] if len(sys.argv) > 1 else None
    rows = {"increment": {}, "convergence": [], "fraction_control": [], "closed_forms": {}}

    for inc in (0, 20, 60, 100, 200, 1000):
        fps = fixed_points(inc)
        traj = simulate(60000, inc, 4000, 1.0)
        rows["increment"][str(inc)] = {
            "fixed_points": fps[:12],
            "fixed_point_count": len(fps),
            "rest_from_60000": traj[-1],
            "min_clock_seen": min(traj),
        }
        print(f"inc={inc:>5}  fixed_points={fps[:8]}{'...' if len(fps) > 8 else ''} "
              f"(n={len(fps)})  rest_from_60000={traj[-1]:.1f} min_seen={min(traj):.1f}")

    print("\ninc=60, always spend the hard limit (the report's claim):")
    for start in (111, 112, 150, 200, 500, 1000, 60000):
        traj = simulate(start, 60, 500, 1.0)
        rec = {
            "start": start, "rest": traj[-1], "min": min(traj),
            "converged_111": abs(traj[-1] - 111.0) < 1e-9,
            "never_below_111": min(traj) >= 111 - 1e-9,
        }
        rows["convergence"].append(rec)
        print(f"  start={start:>6} -> rest={traj[-1]:>8.1f} min={min(traj):>7.1f} "
              f"converged_111={rec['converged_111']} never_below_111={rec['never_below_111']}")

    print("\ninc=60, starting BELOW the floor — the clock must grow, or 111 is not a floor:")
    below = []
    for start in (20, 60, 95, 105, 108, 110, 111):
        traj = simulate(start, 60, 500, 1.0)
        below.append({"start": start, "rest": traj[-1], "grew": traj[-1] > start})
        print(f"  start={start:>4} -> rest={traj[-1]:>8.1f} grew={traj[-1] > start}")
    rows["below_floor"] = below

    print("\ncontrol: same run at 0.2 / 0.6 / 1.0 of the hard limit, inc=60, start=1000:")
    for frac in (0.2, 0.6, 1.0):
        traj = simulate(1000, 60, 500, frac)
        rows["fraction_control"].append({"fraction": frac, "rest": traj[-1], "min": min(traj)})
        print(f"  fraction={frac:<4} -> rest={traj[-1]:>8.1f} min={min(traj):>7.1f}")

    # The two closed forms, stated so their failure is on the record.
    inc = 60
    cf_a = 22 * inc / 5 + 10                      # hard == increment, ignoring the floor()
    cf_b = 22 * (inc // 5) + 9 + OVH              # last clock with hard <= increment
    rows["closed_forms"] = {
        "inc": inc,
        "form_a_hard_equals_increment": cf_a,
        "form_b_last_clock_hard_le_increment": cf_b,
        "simulated_floor": 111,
        "form_a_matches": abs(cf_a - 111) < 0.5,
        "form_b_matches": abs(cf_b - 111) < 0.5,
    }
    print(f"\nclosed forms tried at inc={inc}: A(hard==inc)={cf_a:.1f} "
          f"B(last hard<=inc)={cf_b}  simulated floor=111  "
          f"-> A_matches={abs(cf_a-111) < 0.5} B_matches={abs(cf_b-111) < 0.5}")

    if outpath:
        with open(outpath, "w") as f:
            json.dump(rows, f, indent=2)
        print("\nwrote", outpath)


if __name__ == "__main__":
    main()
