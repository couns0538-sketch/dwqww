"""prof_diff.py - compare two spd_rip_sampler.py result folders (A = lock, B = candidate).

Both exes search the same tree (node-identical), so a difference in cycles is a difference in cost per
unit of the same work. The sampler gives each function's SHARE of its own exe's cycles; to compare the
two exes in the same unit, B's shares are multiplied by B's total cycles relative to A's (--b-over-a,
taken from the A/B cycle measurement: 1 / (1 + delta) for a cycles-NPS delta of B against A).

Output: per function, share in A, scaled share in B, and the difference in percent of A's total cycles.
The differences add up to (b_over_a - 1) * 100. One-sigma sampling error of each row is printed, so a
row can be told from noise.

usage: prof_diff.py DIR_A DIR_B --b-over-a 1.0379 [--table self_by_source_function.tsv] [--top 25]
"""
import argparse
import math
import os


def load(path):
    rows = {}
    total = 0
    with open(path, encoding="utf-8") as f:
        next(f)
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 3:
                continue
            n = int(parts[1])
            rows[parts[2]] = rows.get(parts[2], 0) + n
            total += n
    return rows, total


def main():
    p = argparse.ArgumentParser()
    p.add_argument("a")
    p.add_argument("b")
    p.add_argument("--b-over-a", type=float, required=True)
    p.add_argument("--table", default="self_by_source_function.tsv")
    p.add_argument("--top", type=int, default=25)
    p.add_argument("--tsv", default=None)
    a = p.parse_args()
    ra, na = load(os.path.join(a.a, a.table))
    rb, nb = load(os.path.join(a.b, a.table))
    out = []
    for key in set(ra) | set(rb):
        sa = ra.get(key, 0) / na
        sb = rb.get(key, 0) / nb
        ea = math.sqrt(max(sa * (1 - sa), 0) / na)
        eb = math.sqrt(max(sb * (1 - sb), 0) / nb) * a.b_over_a
        d = sb * a.b_over_a - sa
        out.append((d, sa, sb * a.b_over_a, math.sqrt(ea * ea + eb * eb), key))
    out.sort(key=lambda r: -abs(r[0]))
    print(f"A {na} samples, B {nb} samples, B cycles / A cycles = {a.b_over_a:.4f}; table {a.table}")
    print("delta_pct_of_A  sigma  A_pct  B_scaled_pct  name")
    for d, sa, sb, e, key in out[:a.top]:
        print(f"{100 * d:+7.2f}  {100 * e:5.2f}  {100 * sa:6.2f}  {100 * sb:6.2f}  {key[:110]}")
    print(f"sum of all deltas {100 * sum(r[0] for r in out):+.2f} (expected {100 * (a.b_over_a - 1):+.2f})")
    if a.tsv:
        with open(a.tsv, "w", encoding="utf-8", newline="\n") as f:
            f.write("delta_pct_of_A\tsigma\tA_pct\tB_scaled_pct\tname\n")
            for d, sa, sb, e, key in out:
                f.write(f"{100 * d:+.3f}\t{100 * e:.3f}\t{100 * sa:.3f}\t{100 * sb:.3f}\t{key}\n")


if __name__ == "__main__":
    main()
