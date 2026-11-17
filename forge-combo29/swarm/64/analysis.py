"""Fit the safe-region boundary and report its misclassifications.

The question the brief asks: is the cost a function of Hash, of MultiPV, or of
their product? Three candidate predicates, each fitted on a threshold and scored
by how many grid cells it gets wrong:

  product  : safe  <=>  Hash * MPV  <=  K
  sum      : safe  <=>  Hash + a*MPV <=  K          (a = MPV weight, fitted)
  power    : safe  <=>  Hash * MPV^p <= K           (p fitted; p=1 is product)

A cell is "unsafe" when its median ms exceeds `SLOW_FACTOR` times the median ms of
MultiPV 1 at the SAME Hash (that is the comparison a GUI user feels: same
configured Hash, more lines, slower).

Everything is printed with literal denominators, and the fit is exhaustive over
the candidate thresholds rather than a closed form, so the reported
misclassification count is the true minimum for each family.
"""

from __future__ import annotations

import argparse
import json
import math

SLOW_FACTOR = 1.5


def load(path: str) -> dict:
    with open(path) as fh:
        return json.load(fh)


def table(data: dict) -> dict[tuple[int, int], dict]:
    return {(c["hash"], c["mpv"]): c for c in data["cells"]}


def mpv1_ms(cells: dict, hash_mb: int) -> float | None:
    c = cells.get((hash_mb, 1))
    return c["ms_median"] if c else None


def classify(cells: dict, factor: float) -> dict[tuple[int, int], tuple[bool, float]]:
    """Return {(hash,mpv): (is_safe, ratio_to_mpv1_at_same_hash)}."""
    out = {}
    for (h, m), c in cells.items():
        base = mpv1_ms(cells, h)
        if base is None or base <= 0:
            continue
        ratio = c["ms_median"] / base
        out[(h, m)] = (ratio <= factor, ratio)
    return out


def fit_product(cls: dict) -> tuple[int, int]:
    """Best K for safe <=> Hash*MPV <= K. Returns (K, misclassified)."""
    prods = sorted({h * m for (h, m) in cls})
    best = (None, 10**9)
    for k in prods:
        wrong = sum(1 for (h, m), (safe, _) in cls.items() if (h * m <= k) != safe)
        if wrong < best[1]:
            best = (k, wrong)
    return best  # type: ignore[return-value]


def fit_power(cls: dict, p: float) -> tuple[float, int]:
    """Best K for safe <=> Hash*MPV**p <= K, at a given p."""
    vals = sorted({h * (m ** p) for (h, m) in cls})
    best = (None, 10**9)
    for k in vals:
        wrong = sum(1 for (h, m), (safe, _) in cls.items() if (h * (m ** p) <= k + 1e-9) != safe)
        if wrong < best[1]:
            best = (k, wrong)
    return best  # type: ignore[return-value]


def fit_sum(cls: dict, a: float) -> tuple[float, int]:
    vals = sorted({h + a * m for (h, m) in cls})
    best = (None, 10**9)
    for k in vals:
        wrong = sum(1 for (h, m), (safe, _) in cls.items() if (h + a * m <= k + 1e-9) != safe)
        if wrong < best[1]:
            best = (k, wrong)
    return best  # type: ignore[return-value]


def sweep(cls: dict) -> dict:
    """Exhaustive sweep over the shape parameters, reporting the best of each family."""
    best_power = (None, 10**9, None)
    p = 0.25
    while p <= 4.0 + 1e-9:
        k, wrong = fit_power(cls, p)
        if wrong < best_power[1]:
            best_power = (p, wrong, k)
        p = round(p + 0.05, 4)
    best_sum = (None, 10**9, None)
    a = 0.0
    while a <= 400.0 + 1e-9:
        k, wrong = fit_sum(cls, a)
        if wrong < best_sum[1]:
            best_sum = (a, wrong, k)
        a = round(a + 1.0, 4)
    k_prod, wrong_prod = fit_product(cls)
    return {
        "product": {"K": k_prod, "wrong": wrong_prod},
        "power": {"p": best_power[0], "K": best_power[2], "wrong": best_power[1]},
        "sum": {"a": best_sum[0], "K": best_sum[2], "wrong": best_sum[1]},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--patch", default=None)
    ap.add_argument("--factor", type=float, default=SLOW_FACTOR)
    args = ap.parse_args()

    data = load(args.base)
    cells = table(data)
    total_cells = len(data["cells"])
    n_hash = len(data["hashes"])
    n_mpv = len(data["mpvs"])

    print(f"grid: {n_hash} Hash x {n_mpv} MultiPV = {total_cells} cells (literal)")
    print(f"positions per cell: {len(data['positions'])}  repeats: {data['repeats']}")
    print(f"node budget: {data['nodes_budget']}  slow threshold: {args.factor}x MPV1 at same Hash")

    cls = classify(cells, args.factor)
    unsafe = sum(1 for s, _ in cls.values() if not s)
    print(f"cells classified: {len(cls)}/{total_cells}  unsafe: {unsafe}/{len(cls)}")
    if len(cls) != total_cells:
        print("WARN: some cells had no MPV 1 baseline at their Hash")

    fits = sweep(cls)
    print("\n=== predicate fits (misclassified cells out of %d) ===" % len(cls))
    for name, f in fits.items():
        if name == "product":
            print(f"  product  Hash*MPV <= {f['K']:<5}          wrong {f['wrong']}/{len(cls)}")
        elif name == "power":
            print(f"  power    Hash*MPV^{f['p']:.2f} <= {f['K']:<9.1f} wrong {f['wrong']}/{len(cls)}")
        else:
            print(f"  sum      Hash + {f['a']:.0f}*MPV <= {f['K']:<7.1f} wrong {f['wrong']}/{len(cls)}")

    # Ratio table, the raw evidence the fit is scored against.
    print("\n=== ratio to MPV1 at the same Hash (>1 means slower) ===")
    mpvs = data["mpvs"]
    print("  Hash |" + "".join(f"  MPV{m:<2} " for m in mpvs))
    for h in data["hashes"]:
        row = f"  {h:>4} |"
        for m in mpvs:
            if (h, m) in cls:
                safe, r = cls[(h, m)]
                row += f" {r:>5.2f}{' ' if safe else '!'}"
            else:
                row += "   --  "
        print(row)
    print("  (! = exceeds the threshold; ratio itself printed for every cell)")

    if args.patch:
        pdata = load(args.patch)
        pcells = table(pdata)
        pcls = classify(pcells, args.factor)
        pfits = sweep(pcls)
        print(f"\n=== patched build: {len(pcls)}/{len(pdata['cells'])} cells ===")
        unsafe_p = sum(1 for s, _ in pcls.values() if not s)
        print(f"unsafe after patch: {unsafe_p}/{len(pcls)}  (was {unsafe}/{len(cls)})")
        print("  product  Hash*MPV <= %-5s wrong %d/%d" % (pfits["product"]["K"], pfits["product"]["wrong"], len(pcls)))
        print("  power    Hash*MPV^%.2f <= %.1f wrong %d/%d" % (pfits["power"]["p"], pfits["power"]["K"], pfits["power"]["wrong"], len(pcls)))
        print("  sum      Hash + %.0f*MPV <= %.1f wrong %d/%d" % (pfits["sum"]["a"], pfits["sum"]["K"], pfits["sum"]["wrong"], len(pcls)))
        print("\n=== cells that changed safe/unsafe state ===")
        moved_in = sorted(k for k in pcls if k in cls and pcls[k][0] and not cls[k][0])
        stayed_out = sorted(k for k in pcls if k in cls and not pcls[k][0] and not cls[k][0])
        print(f"  came into the safe region: {len(moved_in)}/{len(pcls)}")
        for h, m in moved_in:
            print(f"    Hash {h:>3} MPV {m}: {cls[(h,m)][1]:.2f}x -> {pcls[(h,m)][1]:.2f}x")
        print(f"  still unsafe: {len(stayed_out)}/{len(pcls)}")
        for h, m in stayed_out:
            print(f"    Hash {h:>3} MPV {m}: {cls[(h,m)][1]:.2f}x -> {pcls[(h,m)][1]:.2f}x")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
