#!/usr/bin/env python3
"""P12: is the own-clock `movestogo 2` gap real, or noise between two builds?

The claim under test. In the §2 table, own-clock `movestogo 2`
(`wtime 2000 btime 2000 movestogo 2`, White to move, plan 663/1592) returned

    379 ms on the base build, 751 ms on the patched build

Both builds contain identical search code paths for this command: the mover's
own clock is given, so `parse_limits` takes the FIRST branch on both, and the
patch's stated invariant is "callers that send their own clock take the first
branch unchanged". A 2x difference would therefore mean the patch changes the
own-clock path, contradicting that invariant.

This script decides it with repeats, interleaved ABBA so drift in machine load
cannot favour either build, and reports each build's spread. If the two builds'
ranges overlap, the 379/751 pair was noise. If they are disjoint, it is real.

Also runs a `go depth` identity control at the same position: a fixed-depth
search must agree between builds (findings §9: the two builds are
interchangeable on non-lone-king positions), which proves the two binaries are
the same search and isolates any difference to time policy.
"""
from __future__ import annotations

import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucilib import Engine, plan_clock  # noqa: E402

FEN = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
OVH = 10
REPS = 12


def engine_ms(r):
    for line in reversed(r.info_lines):
        p = line.split()
        if "time" in p:
            j = p.index("time")
            if j + 1 < len(p):
                try:
                    return int(p[j + 1])
                except ValueError:
                    pass
    return r.wall_ms


def run_arm(exe, spec, reps):
    e = Engine(exe)
    e.set_option("OwnBook", "false")
    e.set_option("Threads", "1")
    e.send(f"position fen {FEN}")
    vals = []
    for _ in range(reps):
        e.send(f"position fen {FEN}")
        r = e.go(spec, timeout=60.0)
        vals.append(engine_ms(r))
    e.close()
    return vals


def depth_control(exe):
    """Fixed-depth identity control: node count must agree between builds."""
    e = Engine(exe)
    e.set_option("OwnBook", "false")
    e.set_option("Threads", "1")
    e.send(f"position fen {FEN}")
    r = e.go("depth 12", timeout=120.0)
    bm = r.bestmove
    nodes = r.nodes
    e.close()
    return {"bestmove": bm, "nodes": nodes}


def main():
    base, patched, outpath = sys.argv[1], sys.argv[2], sys.argv[3]
    rows = []

    # The depth control comes first: if it disagrees, nothing below is attributable.
    d_base = depth_control(base)
    d_patch = depth_control(patched)
    print(f"depth-12 control  base={d_base}  patched={d_patch}  "
          f"identical={d_base == d_patch}")

    spec = "wtime 2000 btime 2000 movestogo 2"
    soft, hard, _ = plan_clock(2000, 0, 2, OVH)
    print(f"arm: go {spec}   plan={soft}/{hard}")

    # Interleaved blocks: ABBA, so a load drift hits both builds equally.
    blocks = [("base", base), ("patched", patched), ("patched", patched), ("base", base)]
    collected = {"base": [], "patched": []}
    for name, exe in blocks:
        vals = run_arm(exe, spec, REPS // 2)
        collected[name].extend(vals)
        print(f"  block {name:<8} vals={vals}")

    for name in ("base", "patched"):
        v = collected[name]
        rows.append({
            "build": name,
            "values": v,
            "n": len(v),
            "min": min(v), "median": statistics.median(v), "max": max(v),
            "mean": round(statistics.mean(v), 1),
            "stdev": round(statistics.stdev(v), 1) if len(v) > 1 else None,
            "plan_soft": soft, "plan_hard": hard,
            "over_hard": sum(1 for x in v if x > hard),
        })
        r = rows[-1]
        print(f"{name:<8} n={r['n']} min={r['min']} med={r['median']} max={r['max']} "
              f"mean={r['mean']} sd={r['stdev']} plan={soft}/{hard} over_hard={r['over_hard']}")

    b, p = rows[0], rows[1]
    overlap = not (b["max"] < p["min"] or p["max"] < b["min"])
    verdict = {
        "ranges_overlap": overlap,
        "base_range": [b["min"], b["max"]],
        "patched_range": [p["min"], p["max"]],
        "medians": [b["median"], p["median"]],
        "depth_control_identical": d_base == d_patch,
        "conclusion": "noise: the two builds' ranges overlap, so the 379/751 pair was not an effect"
                      if overlap else
                      "REAL: the ranges are disjoint, so the patch moves the own-clock path",
    }
    print(f"\noverlap={overlap}  base={b['min']}-{b['max']}  patched={p['min']}-{p['max']}")
    print("conclusion:", verdict["conclusion"])

    with open(outpath, "w") as f:
        json.dump({"fen": FEN, "spec": "go " + spec, "plan": [soft, hard],
                   "reps_per_block": REPS // 2, "rows": rows,
                   "depth_control": {"base": d_base, "patched": d_patch}, "verdict": verdict}, f, indent=2)
    print("wrote", outpath)


if __name__ == "__main__":
    main()
