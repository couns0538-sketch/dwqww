#!/usr/bin/env python3
"""predictor_error.py — how accurate is a naive next-iteration cost predictor?

For every iteration in the committed ladders, predict the NEXT iteration's cost using only information
available at that point, then measure the relative error against the cost that actually happened.

Three predictors:
  global_mean   : one constant, the mean growth ratio over all ladders (a hard-coded constant)
  global_median : one constant, the median growth ratio over all ladders
  local_ratio   : this position's own last growth ratio (c_i / c_{i-1})

Reported: median and percentiles of |predicted/actual - 1|, the fraction within 20 %, and the worst
cases — because the gate's safety depends on the TAIL of this distribution, not its median.

Usage: predictor_error.py
"""
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


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
        costs = []
        prev = 0.0
        for _d, t in seq:
            costs.append(t - prev)
            prev = t
        if len(costs) >= 3:
            out.append((os.path.basename(path), p[0], seq, costs))
    return out


def pct(v, q):
    s = sorted(v)
    k = (len(s) - 1) * q / 100.0
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def main() -> int:
    ladders = []
    for name in ("ladder_base_w10000.tsv", "ladder_PC20_w10000.tsv"):
        path = os.path.join(HERE, name)
        if os.path.exists(path):
            ladders.extend(parse(path))
    if not ladders:
        raise SystemExit("no ladders found")

    # Growth ratios actually observed, for the two global constants.
    ratios = []
    for _f, _i, _seq, costs in ladders:
        for a, b in zip(costs, costs[1:]):
            if a > 5:
                ratios.append(b / a)
    g_mean = statistics.mean(ratios)
    g_med = statistics.median(ratios)
    print(f"growth ratios observed: n={len(ratios)}, mean {g_mean:.3f}, median {g_med:.3f}, "
          f"min {min(ratios):.3f}, max {max(ratios):.3f}")
    print()

    results = {"global_mean": [], "global_median": [], "local_ratio": []}
    worst = {"global_mean": [], "global_median": [], "local_ratio": []}
    for fname, idx, seq, costs in ladders:
        for i in range(1, len(costs) - 1):     # need c_i, c_{i-1} and the actual c_{i+1}
            actual = costs[i + 1]
            if actual <= 5:
                continue
            preds = {"global_mean": g_mean * costs[i], "global_median": g_med * costs[i]}
            if costs[i - 1] > 5:
                preds["local_ratio"] = (costs[i] / costs[i - 1]) * costs[i]
            for k, p in preds.items():
                err = p / actual - 1.0
                results[k].append(abs(err))
                worst[k].append((abs(err), fname, idx, seq[i][0], costs[i], actual, p))

    print("| predictor | n | median |err| | p75 | p90 | p99 | max | within 20 % | within 50 % |")
    print("|---|---|---|---|---|---|---|---|---|")
    for k in ("global_mean", "global_median", "local_ratio"):
        v = results[k]
        if not v:
            continue
        print(f"| {k} | {len(v)} | {pct(v,50)*100:.0f} % | {pct(v,75)*100:.0f} % | "
              f"{pct(v,90)*100:.0f} % | {pct(v,99)*100:.0f} % | {max(v)*100:.0f} % | "
              f"{100.0*sum(1 for x in v if x<=0.20)/len(v):.0f} % | "
              f"{100.0*sum(1 for x in v if x<=0.50)/len(v):.0f} % |")

    print()
    print("## Worst predictions (the tail the gate depends on)")
    print()
    print("| predictor | file | position | at depth | actual cost | predicted | error |")
    print("|---|---|---|---|---|---|---|")
    for k in ("global_mean", "local_ratio"):
        for e, fname, idx, depth, actual, act_next, pred in sorted(worst[k], reverse=True)[:5]:
            print(f"| {k} | {fname[:14]} | #{idx} | {depth} | {actual:.0f} ms | {pred:.0f} ms | "
                  f"{e*100:.0f} % |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
