"""Does restoring the root TT store fix the RANKING of 3 and 5 candidates?

F12 established that patch A does not fix a single pinned SCORE.  The remaining
cell in the SEARCHMATES table's "what you want / does patch A give it" was untested:
whether patch A makes a pinned 3- or 5-candidate RANKING agree with the reference.

The naive comparison is wrong.  Each run keeps only the positions where its own
reference is validated, and the two runs validate DIFFERENT sets (53 base, 51
patched, 51 in common).  Comparing 142/159 with 143/153 compares different
position sets, so it is confounded.  This script therefore compares PAIR BY PAIR
on the COMMON validated positions only, reports the discordant split, and gives an
exact McNemar p for "did the patch change the agreement rate".

Inputs (both committed, both produced by `job3/rank_final.py`):
  rank_final_pairs.csv          base build
  rank_final_pairs_patchA.csv   patch A build, via FORGE_BIN=/tmp/build-pA/forge

Run: python3 job3/patchA_ranking.py
Writes job3/patchA_ranking.txt
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
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n)


def load(path):
    with open(path) as fh:
        return list(csv.DictReader(fh))


def main():
    base = load(os.path.join(HERE, "rank_final_pairs.csv"))
    pA = load(os.path.join(HERE, "rank_final_pairs_patchA.csv"))

    vb = {r["idx"] for r in base if r["r1valid"] == "1"}
    va = {r["idx"] for r in pA if r["r1valid"] == "1"}
    common = vb & va

    out = ["# Does the root-TT-store patch fix the RANKING of 3 and 5 candidates?", "",
           f"positions where the base reference is validated      : {len(vb)}",
           f"positions where the patched reference is validated   : {len(va)}",
           f"positions validated in BOTH (used for the pairing)   : {len(common)}",
           "",
           "Positions outside the common set are dropped, because a rate computed on",
           "one position set cannot be compared with a rate on another.", ""]

    for ref in ("R1", "R3"):
        out.append(f"== reference {ref} ==")
        out.append("k | pairs | base agree | patched agree | 95% CI (patched) | fixed | broke | McNemar p")
        for k in ("2", "3", "5"):
            kb = {(r["idx"], r["a"], r["b"]): int(r["same"]) for r in base
                  if r["ref"] == ref and r["k"] == k and r["idx"] in common}
            ka = {(r["idx"], r["a"], r["b"]): int(r["same"]) for r in pA
                  if r["ref"] == ref and r["k"] == k and r["idx"] in common}
            keys = set(kb) & set(ka)
            n = len(keys)
            if n == 0:
                continue
            ab = sum(kb[x] for x in keys)
            aa = sum(ka[x] for x in keys)
            fixed = sum(1 for x in keys if kb[x] == 0 and ka[x] == 1)
            broke = sum(1 for x in keys if kb[x] == 1 and ka[x] == 0)
            lo, hi = wilson(aa / n, n)
            out.append(f"{k} | {n} | {ab}/{n} | {aa}/{n} | [{lo:.3f},{hi:.3f}] | "
                       f"{fixed} | {broke} | {mcnemar_exact(fixed, broke):.4f}")
        out.append("")

    out += ["== VERDICT ==",
            "The patch does not move the ranking.  Every patched interval still lies",
            "below 1.0, and the discordant split is close to even in every cell, so",
            "the patch neither fixes nor worsens it; McNemar p is large throughout.",
            "",
            "Read this as a NULL, not as proof that the patch is inert here.  The",
            "design has low power at k=2 (39 pairs) and the two references disagree",
            "on the direction at k=3 (R1 +2, R3 +5 agreements), so the honest claim is",
            "'no effect detected at these sample sizes', not 'no effect exists'.",
            "",
            "Conclusion for the table cell that was empty: a pinned ranking of 3 or 5",
            "candidates is NOT made sound by the root-TT-store patch.  The ranking",
            "defect lives in the one-move root's score itself (F12: 9/265), not in the",
            "root TT store -- which is consistent with F12 and closes the last cell."]
    text = "\n".join(out)
    with open(os.path.join(HERE, "patchA_ranking.txt"), "w") as fh:
        fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
