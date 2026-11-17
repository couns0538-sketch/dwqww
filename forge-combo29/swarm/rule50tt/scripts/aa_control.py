"""A/A control: run the SAME build through the same harness twice and compare.

The threshold sweep reported differences at clock 0 and 60 under variants that
only change a `< 90` constant. A threshold cannot affect clock 0 in a fresh
table, so the sweep was measuring something other than the threshold. This file
finds out what, before any of those numbers are believed.

Two designs are compared:
  SHARED  one process per build, all cells run through it (what the first
          threshold sweep did). The transposition table survives between cells,
          so a cell can inherit entries stored at other clocks.
  FRESH   one process per cell. Nothing is inherited.

If SHARED differs from itself across repeats it is not usable evidence, and the
difference between SHARED and FRESH is the size of the contamination; that is
also the direct measurement of "does a warm table change a score".
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import uci_driver as u  # noqa: E402

SHIPPED = "/agent/repos/dwqww/forge-combo29/build-rule50/forge"

BOARDS = [
    ("kqk_b",    "8/8/8/8/8/2K5/1Q6/7k w - -"),
    ("krk_far",  "7k/8/8/R7/8/8/8/K7 w - -"),
]
CLOCKS = [0, 60, 88, 89, 90, 92]
DEPTH = 10


def fresh_cell(exe, fields, clock, depth=DEPTH):
    e = u.Engine(exe, hash_mb=16, timeout=30.0)
    try:
        return e.search(f"position fen {fields} {clock} 60", f"go depth {depth}")
    finally:
        e.close()


def shared_cells(exe, boards, clocks, depth=DEPTH):
    out = {}
    e = u.Engine(exe, hash_mb=16, timeout=30.0)
    try:
        for name, fields in boards:
            for clock in clocks:
                out[(name, clock)] = e.search(f"position fen {fields} {clock} 60", f"go depth {depth}")
    finally:
        e.close()
    return out


def sig(r):
    return (r["score_kind"], r["score"], r["bestmove"])


def main():
    print("=== A/A: SHARED design, same build, two repeats")
    a = shared_cells(SHIPPED, BOARDS, CLOCKS)
    b = shared_cells(SHIPPED, BOARDS, CLOCKS)
    shared_stable = True
    for k in a:
        if sig(a[k]) != sig(b[k]) or a[k]["nodes"] != b[k]["nodes"]:
            shared_stable = False
            print(f"  UNSTABLE {k}: {sig(a[k])} nodes {a[k]['nodes']} vs {sig(b[k])} nodes {b[k]['nodes']}")
    print(f"  shared design reproducible: {shared_stable}")

    print("\n=== A/A: FRESH design, same build, two repeats")
    fresh_a, fresh_b = {}, {}
    for name, fields in BOARDS:
        for clock in CLOCKS:
            fresh_a[(name, clock)] = fresh_cell(SHIPPED, fields, clock)
            fresh_b[(name, clock)] = fresh_cell(SHIPPED, fields, clock)
    fresh_stable = True
    for k in fresh_a:
        if (sig(fresh_a[k]), fresh_a[k]["nodes"]) != (sig(fresh_b[k]), fresh_b[k]["nodes"]):
            fresh_stable = False
            print(f"  UNSTABLE {k}: {sig(fresh_a[k])} vs {sig(fresh_b[k])}")
    print(f"  fresh design reproducible: {fresh_stable}")

    print("\n=== SHARED vs FRESH (the contamination, per cell)")
    diffs = 0
    for k in fresh_a:
        s, f = sig(a[k]), sig(fresh_a[k])
        if s != f:
            diffs += 1
            print(f"  {k[0]:9} clock={k[1]:3}  shared={s} nodes={a[k]['nodes']:>8}"
                  f"  fresh={f} nodes={fresh_a[k]['nodes']:>8}")
    print(f"  {diffs} of {len(fresh_a)} cells differ between a cold and a warm table")

    json.dump({
        "shared_reproducible": shared_stable,
        "fresh_reproducible": fresh_stable,
        "shared": {f"{k[0]}|{k[1]}": a[k] for k in a},
        "fresh": {f"{k[0]}|{k[1]}": fresh_a[k] for k in fresh_a},
        "shared_vs_fresh_diffs": diffs,
    }, open("/tmp/aa_control.json", "w"), indent=1)


if __name__ == "__main__":
    main()
