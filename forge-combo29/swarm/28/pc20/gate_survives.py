#!/usr/bin/env python3
"""gate_survives.py — does the gated rule still make the RIGHT DECISION with a bad predictor?

predictor_error.py shows the naive next-iteration predictor is poor: median absolute error 58 %, p90 138 %,
worst cases over 3000 %. That looks fatal for a rule that projects `t + C*c` and compares against a budget.

But the gate's threshold scales WITH the estimate: the rule stops only when
    (t + C*c_hat) - B >= G * c_hat
which rearranges to a condition on c_hat. So an error in c_hat moves BOTH sides, and the question is
whether the DECISION the rule takes is the same as the decision it would take with a perfect c.

This script answers exactly that, using the recorded ladders:
  - for each iteration, the TRUE cost c is known, so the "oracle" decision is computable;
  - the ESTIMATED cost is the global-median predictor (the best of the three);
  - compare the two decisions: same depth chosen? and if they differ, how much time/ply does the
    disagreement cost?

That is the number that matters for adoption: not predictor accuracy in the abstract, but decision
agreement.

Usage: gate_survives.py [B] [C] [G]
"""
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
B = float(sys.argv[1]) if len(sys.argv) > 1 else 454.0
C = float(sys.argv[2]) if len(sys.argv) > 2 else 1.3
G = float(sys.argv[3]) if len(sys.argv) > 3 else 1.5


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


def decide(seq, budget, growth, gate, est):
    """Return the index of the iteration the rule stops on. `est(i, true_cost)` supplies c_hat."""
    idx = 0
    for i in range(1, len(seq)):
        c_true = seq[i][1] - seq[i - 1][1]
        if c_true <= 0:
            continue
        c_hat = est(c_true)
        proj = seq[i][1] + growth * c_hat
        over = proj - budget
        if over <= 0:
            idx = i
            continue
        if over >= gate * c_hat:
            return i
        idx = i
    return idx


def main() -> int:
    ladders = []
    for name in ("ladder_base_w10000.tsv", "ladder_PC20_w10000.tsv"):
        p = os.path.join(HERE, name)
        if os.path.exists(p):
            ladders.extend(parse(p))

    # The global-median predictor: c_hat = k * c_true, with k the median ratio of predicted/actual.
    # Calibrate k honestly on the same ladders (this is the OPTIMISTIC case for the predictor).
    ratios = []
    for _f, _i, seq in ladders:
        costs, prev = [], 0.0
        for _d, t in seq:
            costs.append(t - prev)
            prev = t
        for a, b in zip(costs, costs[1:]):
            if a > 5 and b > 5:
                ratios.append(b / a)
    k = statistics.median(ratios)
    print(f"best naive predictor: c_hat = {k:.3f} x c_last (median growth, calibrated on this data)")
    print(f"rule: B = {B:.0f}, C = {C}, gate G = {G}")
    print()

    agree = 0
    total = 0
    time_delta = []
    ply_delta = []
    for fname, idx, seq in ladders:
        oracle = decide(seq, B, C, G, lambda c: c)
        naive = decide(seq, B, C, G, lambda c, k=k: k * c)
        total += 1
        if oracle == naive:
            agree += 1
            continue
        td = seq[naive][1] - seq[oracle][1]
        pd = seq[naive][0] - seq[oracle][0]
        time_delta.append(td)
        ply_delta.append(pd)

    print("| metric | value |")
    print("|---|---|")
    print(f"| ladders compared | {total} |")
    print(f"| SAME stopping depth chosen | {agree}/{total} = {100.0*agree/total:.0f} % |")
    if time_delta:
        print(f"| where they differ: median time difference | "
              f"{statistics.median(time_delta):.0f} ms |")
        print(f"| where they differ: median ply difference | "
              f"{statistics.median(ply_delta):+.0f} |")
        print(f"| where they differ: worst ply difference | {max(ply_delta, key=abs):+d} |")
        print(f"| where they differ: worst extra time | {max(time_delta):.0f} ms |")
    print()
    print("A high agreement rate means the gate is implementable with a naive predictor: the predictor's")
    print("error does not change which iteration the search stops on. A low rate means it does, and the")
    print("gate needs a better estimator before it is worth building.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
