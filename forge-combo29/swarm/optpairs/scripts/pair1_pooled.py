"""Pair 1 pooled test: does Hash change the answer at Threads 4 MORE than rerunning does?

The three Threads-4 grids each carry two comparisons on the same positions:

  A/A   the same cell, run in two independent groups of processes
  A/B   two cells that differ only in Hash

Both are reduced to the same statistic -- the fraction of cross-group (run, run)
pairs whose bestmove agrees -- so they are comparable position by position. The
effect of Hash is then the per-position DELTA (A/B agreement - A/A agreement):

  delta < 0   Hash made the move less reproducible than rerunning did
  delta = 0   Hash is indistinguishable from its own noise
  delta > 0   Hash made it MORE reproducible (possible but not expected)

Pooled over 28 positions with a sign-flip permutation test on the mean and a
bootstrap interval. This is the test the naive "differs 12 of 12" count cannot
run, because at Threads 4 the A/A control also "differs 12 of 12".
"""
import json
import os
import random
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.join(os.path.dirname(HERE), "evidence")

# (evidence file, A/A comparison name, A/B comparison name)
ARMS = [
    ("pair1-analysis", "A/A control, Threads 4, Hash 16", "Hash 16 vs 64, Threads 4"),
    ("pair1b-analysis", "A/A control, Threads 4", "Hash 16 vs 256, Threads 4"),
    ("pair1c-analysis", "A/A Threads 4, Hash 1", "Hash 1 vs 256, Threads 4"),
]


def load(name):
    with open(os.path.join(EVID, f"{name}.json")) as fh:
        return json.load(fh)


def per_position(doc, comparison, field="move_agree"):
    for p in doc["pooled"]:
        if p["comparison"] == comparison:
            return {r["position"]: r[field] for r in p["rows"]}
    raise KeyError(comparison)


def main():
    rows = []
    for name, aa_name, ab_name in ARMS:
        doc = load(name)
        aa = per_position(doc, aa_name)
        ab = per_position(doc, ab_name)
        aa_gap = per_position(doc, aa_name, "score_gap_median")
        ab_gap = per_position(doc, ab_name, "score_gap_median")
        for pos in aa:
            rows.append({"grid": name, "position": pos, "aa": aa[pos], "ab": ab[pos],
                         "delta": ab[pos] - aa[pos],
                         "aa_median_score_gap": aa_gap[pos],
                         "ab_median_score_gap": ab_gap[pos]})
    deltas = [r["delta"] for r in rows]
    worse = sum(1 for d in deltas if d < 0)
    better = sum(1 for d in deltas if d > 0)
    equal = len(deltas) - worse - better
    observed = abs(statistics.mean(deltas))

    random.seed(20261117)
    trials = 20000
    hits = 0
    for _ in range(trials):
        flipped = [d * (1 if random.random() < 0.5 else -1) for d in deltas]
        if abs(statistics.mean(flipped)) >= observed:
            hits += 1
    p_value = hits / trials

    boot = []
    for _ in range(5000):
        sample = [random.choice(deltas) for _ in deltas]
        boot.append(statistics.mean(sample))
    boot.sort()
    ci = [boot[int(0.025 * len(boot))], boot[int(0.975 * len(boot)) - 1]]

    # The score-side version of the same question: does Hash widen the score gap?
    score_deltas = [r["ab_median_score_gap"] - r["aa_median_score_gap"] for r in rows]

    out = {"positions": len(rows),
           "worse": worse, "better": better, "equal": equal,
           "mean_delta": statistics.mean(deltas), "sd_delta": statistics.stdev(deltas),
           "permutation_p_two_sided": p_value, "bootstrap_ci95": ci,
           "mean_score_gap_delta": statistics.mean(score_deltas),
           "rows": rows}
    with open(os.path.join(EVID, "pair1-pooled.json"), "w") as fh:
        json.dump(out, fh, indent=1)

    print(f"Pooled Hash x Threads test, {len(rows)} positions from 3 grids")
    print(f"  A/B agreement worse than A/A: {worse}   better: {better}   equal: {equal}")
    print(f"  mean delta {statistics.mean(deltas):+.4f}  (sd {statistics.stdev(deltas):.4f})")
    print(f"  sign-flip permutation p = {p_value:.4f}   bootstrap 95% CI [{ci[0]:+.4f}, {ci[1]:+.4f}]")
    print(f"  score-gap delta (A/B minus A/A), median-of-medians: {statistics.mean(score_deltas):+.2f} cp")
    print("  verdict: Hash at Threads 4 is", "indistinguishable from its own noise"
          if p_value > 0.05 else "measurably different", "on moves")


if __name__ == "__main__":
    sys.exit(main())
