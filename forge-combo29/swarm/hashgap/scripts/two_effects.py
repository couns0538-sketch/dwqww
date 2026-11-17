"""Separate the two effects the geometry control exposed.

The 64-vs-65 pair answers "does a size change alone diverge?" but it does not
answer "does load add anything on top?"  On the same 24 positions at 2M nodes:

  64 vs 65   10/24 disagree, both tables nearly empty and equally loaded
  16 vs 64   20/24 disagree, one table much fuller

So the correct statement is not "collisions are irrelevant" and not "collisions
are the cause". It is a baseline divergence from remapping plus an additional
increment that tracks load. This script measures both increments on one position
set and puts a confidence interval on each, so the report cannot round either
into the other.

Fisher's exact test is computed directly; no scipy on this machine.
"""

import json
import sys
from math import comb

NODES = 2000000


def fisher_two_sided(a, b, c, d):
    """Two-sided Fisher exact p for the 2x2 table [[a,b],[c,d]]."""
    n = a + b + c + d
    row1 = a + b
    col1 = a + c
    total = comb(n, row1)

    def prob(x):
        return comb(col1, x) * comb(n - col1, row1 - x) / total

    observed = prob(a)
    lo = max(0, row1 + col1 - n)
    hi = min(row1, col1)
    p = sum(prob(x) for x in range(lo, hi + 1) if prob(x) <= observed + 1e-12)
    return min(1.0, p)


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def main():
    binary = sys.argv[1]
    out_path = sys.argv[2]
    position_file = sys.argv[3]
    count = int(sys.argv[4]) if len(sys.argv) > 4 else 24

    fens = []
    with open(position_file) as handle:
        for line in handle:
            line = line.strip()
            if line and not line.startswith("#"):
                fens.append(line)
                if len(fens) >= count:
                    break

    sizes = [16, 32, 64, 65, 96, 256]
    rows = []
    for fen in fens:
        for size in sizes:
            import ucih
            cell = ucih.one_cell(binary, fen, f"go nodes {NODES}", size)
            trace = cell["trace"] or {}
            deep = sum(c for depth, c in (trace.get("displaced_depth") or {}).items()
                       if int(depth) >= 1)
            rows.append({
                "fen": fen, "hash": size, "bestmove": cell["bestmove"],
                "score": cell["score"], "deep_evictions": deep,
                "total_displace": trace.get("store_displace"),
            })
        print(f"  {len(rows)} cells", flush=True)

    with open(out_path, "w") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")

    by_key = {(r["fen"], r["hash"]): r for r in rows}

    print(f"\n## Divergence from Hash 64 at go nodes {NODES}, {len(fens)} positions\n")
    print("| size | disagree | 95% CI | mean real evictions | vs the 64/65 baseline (Fisher p) |")
    print("|---|---|---|---|---|")

    def differs(fen, size):
        a = by_key[(fen, size)]
        b = by_key[(fen, 64)]
        return a["bestmove"] != b["bestmove"] or a["score"] != b["score"]

    n = len(fens)
    k0 = sum(1 for fen in fens if differs(fen, 65))

    for size in sizes:
        if size == 64:
            continue
        k = sum(1 for fen in fens if differs(fen, size))
        lo, hi = wilson(k, n)
        deep = sum(by_key[(fen, size)]["deep_evictions"] for fen in fens) / n
        if size == 65:
            p_text = "baseline"
        else:
            p = fisher_two_sided(k, n - k, k0, n - k0)
            p_text = f"p = {p:.4g}"
        print(f"| {size} | **{k}/{n}** | [{lo*100:.0f}%, {hi*100:.0f}%] | {deep:.0f} | {p_text} |")

    print("\n## Reading\n")
    print("The 65 row is the cost of changing geometry alone: same load, all keys")
    print("remapped. A row with a materially higher rate and a small p is where load")
    print("adds on top of that baseline.")


if __name__ == "__main__":
    main()
