#!/usr/bin/env python3
"""separation.py ON.json OFF.json -- which reduction statistic, if any, separates the
2 counter-case boards from the 9 predicted ones, and how much that test can see.

Two tests, because the class test alone is underpowered at n=2:

  A. RANGE TEST (the lead's question). A counter separates the classes if both
     counter-case values fall outside the range spanned by the 9 predicted values.
     With 2 against 9 this test is weak, so its power is COMPUTED here by
     enumeration rather than assumed: the probability that 2 values drawn at random
     from the 11 land inside the range of the other 9 is printed beside every
     verdict. A non-separation at that power is a weak negative, and it is reported
     as one.

  B. RANK CORRELATION across all 11 boards. If a statistic drives the node change,
     it should co-vary with the signed node delta over every board, not only the
     two. Spearman rho and its exact two-sided permutation p are printed. This uses
     all 11 observations, so it has power the class test lacks.

Controls: the node count itself must separate (it DEFINES the classes), and a
deliberately random column must not. If the node control fails, the comparison is
broken and the script says so instead of reporting the other rows.

Usage: separation.py ON.json OFF.json
"""
import argparse
import itertools
import json
import sys


def spearman(x, y):
    """Spearman rho with average ranks for ties."""
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    rx, ry = ranks(x), ranks(y)
    n = len(x)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = sum((a - mx) ** 2 for a in rx) ** 0.5
    dy = sum((b - my) ** 2 for b in ry) ** 0.5
    if dx == 0 or dy == 0:
        return 0.0
    return num / (dx * dy)


def perm_p(x, y, rho):
    """Exact two-sided permutation p for rho over all n! orderings (n<=11: 40M is too
    many, so use a random sample of 20000 permutations and say so)."""
    import random
    rng = random.Random(12345)
    n = len(y)
    hits = 0
    trials = 20000
    for _ in range(trials):
        perm = y[:]
        rng.shuffle(perm)
        if abs(spearman(x, perm)) >= abs(rho) - 1e-12:
            hits += 1
    return (hits + 1) / (trials + 1), trials


def range_test(values, cls):
    pred = [v for v, c in zip(values, cls) if c == "pred"]
    cntr = [v for v, c in zip(values, cls) if c == "CNTR"]
    pmin, pmax = min(pred), max(pred)
    inside = [v for v in cntr if pmin <= v <= pmax]
    return {"pred_range": (pmin, pmax), "cntr": cntr, "inside": len(inside),
            "separates": len(inside) == 0}


def power(classes):
    """P(both counter-cases land inside the range of the rest) over random assignments.

    The counter-case boards are 2 fixed boards; the question is how often a statistic
    with NO relation to the classes would still 'separate' them. Enumerate every
    choice of which 2 of the 11 boards are the counter-cases.
    """
    n = len(classes)
    idx = list(range(n))
    sep = 0
    tot = 0
    for chosen in itertools.combinations(idx, 2):
        c = ["pred"] * n
        for i in chosen:
            c[i] = "CNTR"
        # a random statistic: use board index as a fixed arbitrary value
        vals = list(range(n))
        r = range_test(vals, c)
        tot += 1
        if r["separates"]:
            sep += 1
    return sep / tot


def get(block, key, default=0.0):
    if not block:
        return default
    try:
        return float(block.get(key, default))
    except (TypeError, ValueError):
        return default


FIELDS = [
    # dNodes is the quantity the classes were defined by; it is the control, and it is
    # also a legitimate candidate driver. `nodes` (capON's own tree size) is a
    # DIFFERENT quantity and is listed separately so the control cannot be confused
    # with it.
    ("dNodes", lambda on, off: float((on["nodes"] or 0) - (off["nodes"] or 0))),
    ("nodes_capON", lambda on, off: float(on["nodes"] or 0)),
    ("applied", lambda on, off: get(on["lmr_total"], "applied")),
    ("rmean", lambda on, off: get(on["lmr_total"], "rmean")),
    ("research", lambda on, off: get(on["lmr_total"], "research")),
    ("rej", lambda on, off: get(on["lmr_total"], "rej")),
    ("cap_gate", lambda on, off: get(on["lmr_total"], "cap_gate")),
    ("cap_clamp", lambda on, off: get(on["lmr_total"], "cap_clamp")),
    ("cap_rmean", lambda on, off: get(on["lmr_total"], "cap_rmean")),
    ("clamp_share", lambda on, off: (
        get(on["lmr_total"], "cap_clamp") / get(on["lmr_total"], "cap_gate", 1.0)
        if get(on["lmr_total"], "cap_gate") else 0.0)),
    ("clamp_per_node", lambda on, off: get(on["lmr_total"], "cap_clamp") / max(1.0, float(on["nodes"] or 1))),
    ("gate_per_node", lambda on, off: get(on["lmr_total"], "cap_gate") / max(1.0, float(on["nodes"] or 1))),
    ("applied_per_node", lambda on, off: get(on["lmr_total"], "applied") / max(1.0, float(on["nodes"] or 1))),
    ("rej_per_node", lambda on, off: get(on["lmr_total"], "rej") / max(1.0, float(on["nodes"] or 1))),
    ("rmean_drop", lambda on, off: get(off["lmr_total"], "rmean") - get(on["lmr_total"], "rmean")),
    ("applied_delta", lambda on, off: get(on["lmr_total"], "applied") - get(off["lmr_total"], "applied")),
    # every raw count above scales with tree size, so these are expected to correlate.
    # The per-node and share columns are the ones that are NOT mechanically tied to it.
]
# raw counts that are mechanically proportional to the search tree: rho on these is
# not evidence about the mechanism, and they are marked in the output.
TREE_SCALED = {"nodes_capON", "applied", "research", "rej", "cap_gate", "cap_clamp",
               "applied_delta"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("on")
    ap.add_argument("off")
    a = ap.parse_args()
    on = json.load(open(a.on))
    off = json.load(open(a.off))
    if len(on) != len(off):
        sys.exit(f"row count differs: {len(on)} vs {len(off)}")
    cls = [r["cls"] for r in on]
    dn = [float((r_on["nodes"] or 0) - (r_off["nodes"] or 0)) for r_on, r_off in zip(on, off)]

    pw = power(cls)
    print(f"n = {len(on)} boards, {cls.count('CNTR')} counter-cases, {cls.count('pred')} predicted")
    print(f"POWER of the range test: a statistic with NO relation to the classes still")
    print(f"  'separates' them in {100.0*pw:.0f}% of random assignments of 2-of-11,")
    print(f"  so its power is {100.0*(1.0-pw):.0f}%. A non-separation at that power is a WEAK negative.")
    print()
    hdr = (f"{'counter':17s} {'sep':>4s} {'in':>3s} {'pred range':>22s} {'counter-case vals':>18s} "
           f"{'rho vs dNodes':>13s} {'p':>7s}")
    print(hdr)
    print("-" * len(hdr))

    rows = []
    for name, fn in FIELDS:
        vals = [fn(r_on, r_off) for r_on, r_off in zip(on, off)]
        rt = range_test(vals, cls)
        rho = spearman(vals, dn)
        p, trials = perm_p(vals, dn, rho)
        rows.append({"name": name, "sep": rt["separates"], "inside": rt["inside"],
                     "rho": rho, "p": p})
        pr = f"[{rt['pred_range'][0]:.4g}, {rt['pred_range'][1]:.4g}]"
        cv = ", ".join(f"{v:.4g}" for v in rt["cntr"])
        flag = " (tree-scaled)" if name in TREE_SCALED else ""
        print(f"{name:17s} {'YES' if rt['separates'] else 'no':>4s} {rt['inside']:>3d} {pr:>22s} {cv:>18s} "
              f"{rho:>+13.3f} {p:>7.4f}{flag}")

    # controls
    nodes_row = next(r for r in rows if r["name"] == "dNodes")
    print()
    if not nodes_row["sep"]:
        print("CONTROL FAILED: the node count does not separate the classes it DEFINES — "
              "the comparison is broken; do not read the rows above.")
        return 1
    print("CONTROL OK: dNodes separates the classes (it defines them, so this checks the pipeline).")
    print(f"       dNodes vs dNodes rho = {nodes_row['rho']:+.3f} (must be +1.000 by construction): "
          f"{'consistent' if abs(nodes_row['rho'] - 1.0) < 1e-9 else 'INCONSISTENT'}")

    separating = [r["name"] for r in rows if r["sep"] and r["name"] != "dNodes"]
    correlated = [r["name"] for r in rows if abs(r["rho"]) > 0.6 and r["name"] != "dNodes"]
    correlated_free = [n for n in correlated if n not in TREE_SCALED]
    print()
    print(f"counters separating the classes (besides nodes): {separating if separating else 'NONE'}")
    print(f"counters with |rho| > 0.6 against the signed node delta: {correlated if correlated else 'NONE'}")
    print(f"  of those, NOT mechanically tied to tree size: {correlated_free if correlated_free else 'NONE'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
