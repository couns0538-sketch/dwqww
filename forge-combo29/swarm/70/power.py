"""Power of every discriminator used in this audit, computed before the verdicts
are written down.  A discriminator that cannot separate the two hypotheses at the
sample size actually run is not evidence, whatever it returns.

Run: python3 power.py
Writes power.txt
"""
import math
import os


def wilson_ci(p, n, z=1.96):
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    s = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - s) / d, (c + s) / d)


def width(p, n):
    lo, hi = wilson_ci(p, n)
    return hi - lo


def main():
    out = ["# Power of each discriminator", ""]

    out += ["## D1  order vs search (job1/order_vs_search.py)",
            "Hypothesis A (order): a changed bestmove keeps the SAME score.",
            "Hypothesis B (search): a changed bestmove carries a DIFFERENT score.",
            "Statistic: fraction of changed-bestmove cases with unchanged score.",
            "",
            "sample size actually run: 120 searches, 22 with a changed bestmove.",
            f"95% Wilson interval on 0/22 : {wilson_ci(0.0, 22)[0]:.3f}..{wilson_ci(0.0, 22)[1]:.3f}",
            "A under the data would need that fraction to be 1.0.  The interval's",
            "upper bound is far below 1.0, so A is rejected; B is the survivor.",
            "The test is decisive at n=22 because A makes a point prediction (1.0).",
            ""]

    out += ["## D2  root TT store as the mechanism (job1/causal_split.py)",
            "Hypothesis A: the restricted root's missing TT store causes the change.",
            "Hypothesis B: the IIR depth reduction at a restricted root causes it.",
            "Four arms over the same 60 positions at depth 12, all with the all-legal",
            "restriction: base_all, pA_all (TT store restored), pB_all (IIR spared),",
            "pAB_all (both).",
            "",
            "Statistic: bestmove identical to the plain search, and score identical.",
            "",
            "  base_all  49/60 moves, 1/60 scores",
            "  pA_all    60/60 moves, 60/60 scores   <- TT store alone explains everything",
            "  pB_all    51/60 moves, 7/60 scores    <- IIR is a minor secondary",
            "  pAB_all   60/60 moves, 60/60 scores",
            "",
            "Under hypothesis A the prediction is pA_all = plain exactly, which is what",
            "happened: 0 discordant positions out of 60, and the score column goes from",
            "1/60 to 60/60.  The probability that restoring the TT store would fix both",
            "move and score on 60 consecutive positions by chance, given the base rate",
            "of 1/60 scores, is vanishing; A is accepted and B is a contributor only.",
            ""]

    out += ["## D3  rank order over k candidates (job3/rank_final.py)",
            "k=3: 159 pair comparisons; k=5: 530.  Both after restricting to",
            "positions where the reference is validated (53 of 60).",
            "Claim tested: pinning preserves rank order (rate 1.0).",
            f"observed 142/159 -> 95% CI {wilson_ci(142 / 159, 159)[0]:.3f}..{wilson_ci(142 / 159, 159)[1]:.3f}",
            f"observed 486/530 -> 95% CI {wilson_ci(486 / 530, 530)[0]:.3f}..{wilson_ci(486 / 530, 530)[1]:.3f}",
            "Both intervals exclude 1.0, so 'preserved' is rejected at both k.",
            "Power to detect a drop to 0.90: at n=530 a 0.90 rate gives a CI half-width",
            f"of {width(0.90, 530) / 2:.3f}, so a true 1.0 and a true 0.90 are separable.",
            ""]

    out += ["## D4  the verifier's own operation (job3/verifier_operation.py)",
            "Statistic: positions where pinning each candidate alone makes the plain",
            "bestmove the highest-scoring candidate.  Denominator 60.",
            f"observed 49/60 -> 95% CI {wilson_ci(49 / 60, 60)[0]:.3f}..{wilson_ci(49 / 60, 60)[1]:.3f}",
            "This one needs no reference at all: the reference is the plain search,",
            "which job3 measured deterministic at 60/60.  Its power is limited only by",
            "the 60 positions, and the observed rate is far from 1.0.",
            ""]

    out += ["## D5  pinned score vs in-tree score (job1/pinned_vs_intree.py)",
            "Statistic: fraction of (move, position) pairs whose pinned score equals",
            "the score that move got inside an unrestricted search.",
            f"observed 10/265 -> 95% CI {wilson_ci(10 / 265, 265)[0]:.4f}..{wilson_ci(10 / 265, 265)[1]:.4f}",
            "265 pairs is a large sample; the interval is narrow enough that no",
            "threshold anywhere near 'identity' survives.",
            ""]

    out += ["## Where this audit is NOT decisive",
            "* k=2 at 47/53 and 48/53: the intervals reach up to 0.947-0.959, so a true",
            "  rate of 0.95 is NOT excluded.  The coordinator's 8/8 at two candidates is",
            "  therefore not contradicted by a decisive margin -- but it is also not",
            "  confirmed at 100%: 6 of 60 positions DO contradict it (D4).",
            "* Nothing here says which consumer needs which accuracy.  A consumer that",
            "  only needs 'which of these two is better, when they differ by >= 100 cp'",
            "  is served (313/317 = 0.987 in job3/rank_why.txt).  A consumer that needs",
            "  the top pair when they differ by ~10 cp is not.",
            ]
    text = "\n".join(out)
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "power.txt"), "w") as fh:
        fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
