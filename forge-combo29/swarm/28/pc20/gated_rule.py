#!/usr/bin/env python3
"""gated_rule.py — the gated soft stop rule vs the ungated one, from the committed ladders.

Both rules act at ITERATION BOUNDARIES. Notation, per position from its ladder (depth_i, t_i) with
iteration costs c_i = t_i - t_{i-1}:

  projection   P_i = t_i + C * c_i        (what the NEXT iteration is expected to finish at, C = growth 1.3)
  overshoot    O_i = P_i - B              (how far past the budget B that projection lands)

  UNGATED rule:  stop at iteration i whenever P_i > B.   That is exactly "refuse to start an iteration
                 that cannot finish inside the budget".
  GATED rule:    stop at iteration i only when P_i > B AND O_i >= G * c_i  (G = 2).
                 Where the projection misses the budget by a small amount, the gated rule does NOT stop:
                 it risks the iteration, because a near-miss often completes anyway.

Why that gate is the candidate the owner asked me to test: the searches the ungated rule cuts at a cost of
2-3 plies are the ones where the next iteration only just missed the budget, so several cheap iterations
would still have fitted. Where the projection badly overshoots (the S-F31 case: 565 ms spent, nothing
gained), stopping costs nothing.

Reported per rule: total time saved against the actual search, plies lost, and how the savings distribute
across the ply-cost classes. Both computed from the SAME ladders, so the comparison is apples to apples.

B is the soft plan. C = 1.3 is the median growth factor measured in S-F26/S-F27.

Usage: gated_rule.py [B] [C] [G]
"""
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def parse(path):
    rows = []
    for line in open(path).read().splitlines()[1:]:
        p = line.split("\t")
        if len(p) < 6:
            continue
        seq = []
        for tok in p[1].split():
            d, t = tok.split(":")
            seq.append((int(d), float(t)))
        if len(seq) >= 2:
            rows.append((p[0], seq))
    return rows


def rule_stop(seq, budget, growth, gate):
    """Return the index of the last iteration the rule allows to be the stopping point."""
    idx = 0
    for i in range(1, len(seq)):
        c = seq[i][1] - seq[i - 1][1]
        if c <= 0:
            continue
        proj = seq[i][1] + growth * c
        over = proj - budget
        if over <= 0:
            idx = i
            continue
        # projection misses the budget
        if gate is None:
            return i          # ungated: stop here
        if over >= gate * c:
            return i          # gated: stop only on a decisive miss
        idx = i               # near miss: risk it and continue
    return idx


def run(rows, budget, growth, gate, label):
    saved, lost, stops = [], [], []
    for _idx, seq in rows:
        actual_depth, actual_time = seq[-1]
        i = rule_stop(seq, budget, growth, gate)
        stop_depth, stop_time = seq[i]
        saved.append(actual_time - stop_time)
        lost.append(actual_depth - stop_depth)
        stops.append((stop_time, stop_depth, actual_time, actual_depth))
    return {"label": label, "saved": saved, "lost": lost, "stops": stops}


def describe(r):
    s, l = r["saved"], r["lost"]
    return (f"| {r['label']} | {statistics.median(s):.0f} | {statistics.mean(s):.0f} | {max(s):.0f} | "
            f"{statistics.median(l):.0f} | {statistics.mean(l):.2f} | {max(l)} | "
            f"{sum(1 for x in l if x == 0)} | {sum(1 for x in l if x == 1)} | "
            f"{sum(1 for x in l if x >= 2)} |")


def main() -> int:
    budget = float(sys.argv[1]) if len(sys.argv) > 1 else 454.0
    growth = float(sys.argv[2]) if len(sys.argv) > 2 else 1.3
    gate = float(sys.argv[3]) if len(sys.argv) > 3 else 2.0

    print(f"budget B = {budget:.0f} ms (soft), growth C = {growth}, gate G = {gate}")
    print("Both rules act only at iteration boundaries; both computed from the same ladders.")
    print()
    print("| build | rule | saving median | saving mean | saving max | plies lost median | "
          "mean | max | lose 0 | lose 1 | lose 2+ |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    allrows = {}
    for name, label in (("ladder_base_w10000.tsv", "base"), ("ladder_PC20_w10000.tsv", "PC20")):
        path = os.path.join(HERE, name)
        if not os.path.exists(path):
            continue
        rows = parse(path)
        allrows[label] = rows
        for gate_value, rlabel in ((None, "ungated"), (gate, f"gated G={gate:g}")):
            r = run(rows, budget, growth, gate_value, rlabel)
            print(f"| {label} " + describe(r))

    # The comparison that decides the recommendation: among the searches each rule touches,
    # what does the gated rule give up and keep?
    print()
    print("## Where the two rules disagree")
    print()
    print("| build | searches where gated saves less | median extra saving of ungated | "
          "median extra ply cost of ungated | verdict |")
    print("|---|---|---|---|---|")
    for label, rows in allrows.items():
        u = run(rows, budget, growth, None, "u")
        g = run(rows, budget, growth, gate, "g")
        diffs = [(gu - gg, uu + uu2) for gu, gg, uu, uu2 in
                 zip(u["saved"], g["saved"], u["lost"], g["lost"])]
        worse = [d for d in diffs if d[0] > 1.0]
        extra_save = statistics.median([d[0] for d in worse]) if worse else 0
        extra_ply = statistics.median([d[1] for d in worse]) if worse else 0
        if not worse:
            verdict = "identical on this set"
        elif extra_ply <= 0 and extra_save > 0:
            verdict = "UNGATED is better (more saving, no extra ply)"
        elif extra_save > 0 and extra_ply > 0:
            verdict = "trade-off: ungated buys time with plies"
        else:
            verdict = "GATED is better"
        print(f"| {label} | {len(worse)} | {extra_save:.0f} ms | {extra_ply:.1f} | {verdict} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
