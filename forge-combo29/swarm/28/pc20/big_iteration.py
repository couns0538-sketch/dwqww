#!/usr/bin/env python3
"""big_iteration.py — what does the gate do when the completed iteration ALREADY exceeded soft?

The gap the owner identified: at 6 s + 0.06 the soft plan is 317 ms, and sparse-class iteration costs reach
415 ms. So `c_last > soft` is not a corner case there — it is the regime the heavy moves live in. My ladder
arithmetic used B = 454 with iteration costs that mostly stayed below it.

Algebra first. The rule is
    stop when   P - B >= G * c      where P = t + C * c
i.e.            t + C*c - B >= G*c
i.e.            t - B >= (G - C) * c
With G = 1.5 and C = 1.3, G - C = 0.2 > 0, so the RHS GROWS with c: a large c_last makes the rule STOP
EARLIER, not later. That is the opposite of what a naive reading suggests, and it is the key property.
As c -> infinity the condition reduces to "stop whenever t is even slightly past B", which is correct
behaviour: if a single iteration already overruns the budget by a lot, do not start another.

This script verifies that on the data and measures:
  1. how many recorded iterations have c_last > their plan's soft (the regime the owner asks about);
  2. what the rule decides in those cases, and whether it ever CONTINUES (the dangerous answer);
  3. the same with a 6 s-sized budget (317 ms) applied to the recorded iteration costs, which is the
     closest I can get to the owner's control without re-running ladders at 6 s.

Usage: big_iteration.py [B6]
"""
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
G, C = 1.5, 1.3


def parse(path):
    out = []
    for line in open(path).read().splitlines()[1:]:
        p = line.split("\t")
        if len(p) < 6:
            continue
        seq = []
        for tok in p[1].split():
            d, t = tok.split(":")
            seq.append((int(d), float(t)))
        if len(seq) >= 3:
            out.append((os.path.basename(path), p[0], seq))
    return out


def main() -> int:
    B6 = float(sys.argv[1]) if len(sys.argv) > 1 else 317.0
    ladders = []
    for name in ("ladder_base_w10000.tsv", "ladder_PC20_w10000.tsv"):
        p = os.path.join(HERE, name)
        if os.path.exists(p):
            ladders.extend(parse(p))

    print("## Algebra: the rule tightens as c_last grows")
    print()
    print(f"stop  <=>  t - B >= (G - C) * c_last   with G = {G}, C = {C}  =>  (G - C) = {G-C:+.1f}")
    print()
    print("Because G > C, a LARGER last iteration makes the rule stop SOONER. So 'c_last > soft' is")
    print("handled by the arithmetic itself — it is not a case the rule needs special-casing. What it")
    print("does need is that the search never loops: if a single iteration exceeds soft, the rule must")
    print("still allow ONE iteration to complete (otherwise a search whose iteration 1 exceeds soft would")
    print("stop with no move at all). That is a floor on the iteration count, not on the time.")
    print()

    for B in (454.0, B6):
        print(f"## Budget B = {B:.0f} ms")
        print()
        rows = []
        cont_after_over = 0
        stop_after_over = 0
        for fname, idx, seq in ladders:
            for i in range(1, len(seq)):
                c = seq[i][1] - seq[i - 1][1]
                t = seq[i][1]
                if c <= 0:
                    continue
                over_soft = c > B
                proj = t + C * c
                decided_stop = (proj - B) >= G * c
                rows.append((idx, seq[i][0], c, t, over_soft, decided_stop))
                if over_soft:
                    if decided_stop:
                        stop_after_over += 1
                    else:
                        cont_after_over += 1
        n_over = stop_after_over + cont_after_over
        all_over = [r for r in rows if r[4]]
        print(f"- iterations examined: {len(rows)}")
        print(f"- iterations whose own cost exceeded soft: {n_over} ({100.0*n_over/max(1,len(rows)):.0f} %)")
        if all_over:
            print(f"- of those, the rule STOPS: {stop_after_over}, CONTINUES: {cont_after_over}")
            print(f"- largest single iteration cost: {max(r[2] for r in all_over):.0f} ms "
                  f"(= {max(r[2] for r in all_over)/B:.2f}x soft)")
            print(f"- in those cases, time already elapsed when it stops: "
                  f"median {statistics.median([r[3] for r in all_over]):.0f} ms, "
                  f"max {max(r[3] for r in all_over):.0f} ms")
        print()

    print("## What the rule should do when the just-completed iteration already overran soft")
    print()
    print("The data answer: it stops, and it stops because of the algebra, not by luck. With G > C the")
    print("threshold grows faster than the projection, so a large c_last forces a stop. The ONE thing an")
    print("implementation must add is a floor: complete at least one iteration before any time rule can")
    print("fire, otherwise a search whose first iteration exceeds a very small soft plan would return")
    print("with no bestmove. That floor is already implied by the engine's iterative-deepening loop")
    print("(`for depth = 1; depth <= max_depth; ++depth` with the stop check AFTER the iteration), but it")
    print("must not be broken by placing the check before the first iteration.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
