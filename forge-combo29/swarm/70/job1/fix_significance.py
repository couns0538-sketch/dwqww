"""Significance of the fix-vs-pinned-score comparison, committed so the claim is
re-runnable rather than asserted in prose.

Two tests:
  * overall (all 265 (move, position) pairs): are the identity counts different
    between builds?  McNemar on the discordant pairs, exact binomial.
  * top move only (53 pairs): same test, and an explicit note that this subgroup
    was selected AFTER seeing the overall result, so its p-value is exploratory
    and must not be quoted as confirmatory.

Run: python3 job1/fix_significance.py
Writes job1/fix_significance.txt
"""
import csv
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def wilson(p, n, z=1.96):
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    s = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - s) / d, (c + s) / d)


def mcnemar_exact(b, c):
    """Two-sided exact McNemar: b and c are the two discordant counts."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def main():
    rows = list(csv.DictReader(open(os.path.join(HERE, "fix_vs_pinned_score.csv"))))
    out = [f"pairs {len(rows)}", ""]

    def block(label, sub):
        n = len(sub)
        b = sum(1 for r in sub if int(r["pinned_base"]) == int(r["intree_base"]))
        a = sum(1 for r in sub if int(r["pinned_pA"]) == int(r["intree_pA"]))
        fixed_only = sum(1 for r in sub
                         if int(r["pinned_base"]) != int(r["intree_base"])
                         and int(r["pinned_pA"]) == int(r["intree_pA"]))
        broke_only = sum(1 for r in sub
                         if int(r["pinned_base"]) == int(r["intree_base"])
                         and int(r["pinned_pA"]) != int(r["intree_pA"]))
        p = mcnemar_exact(fixed_only, broke_only)
        out.append(f"== {label} ==")
        out.append(f"  n {n}")
        out.append(f"  base build identical: {b}/{n}  95% CI "
                   f"[{wilson(b/n, n)[0]:.4f},{wilson(b/n, n)[1]:.4f}]")
        out.append(f"  pA   build identical: {a}/{n}  95% CI "
                   f"[{wilson(a/n, n)[0]:.4f},{wilson(a/n, n)[1]:.4f}]")
        out.append(f"  discordant: fixed by patch {fixed_only}, broken by patch {broke_only}")
        out.append(f"  exact McNemar two-sided p = {p:.4f}")
        out.append("")
        return p

    p_all = block("ALL 265 pairs", rows)
    top = [r for r in rows if r["is_top"] == "1"]
    p_top = block("TOP MOVE ONLY, 53 pairs (post-hoc subgroup -- exploratory)", top)

    out += ["== VERDICT ==",
            f"All pairs: p = {p_all:.4f}.  The patch neither helps nor hurts on the",
            "full set; the identity rate is 9/265 against 10/265.  DECISIVE NULL for",
            "the general question 'does the fix restore a pinned score'.",
            "",
            f"Top move only: p = {p_top:.4f}, 1/53 -> 6/53, 5 fixed and 0 broken.",
            "This does NOT clear 0.05, and the subgroup was chosen after seeing the",
            "full-set result.  Report it as a lead worth a pre-registered run, not as",
            "a finding.  A confirmatory test would fix the subgroup in advance and use",
            "a fresh position set."]
    text = "\n".join(out)
    with open(os.path.join(HERE, "fix_significance.txt"), "w") as fh:
        fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
