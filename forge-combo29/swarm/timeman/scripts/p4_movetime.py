#!/usr/bin/env python3
"""P4: movetime accuracy as a FLOOR and a CEILING, not an average.

Why not a mean: a clock move costs its last completed iteration, so wall time is
a step function of the request. Averaging ratios across 10/50/100 ms mixes
granularity regimes and the mean is dominated by whichever regime the sample
happened to sit in. So this reports, per request:

    ratio = wall_ms / requested_ms
    min   = floor   (the fastest the engine can possibly return)
    max   = ceiling (the worst overshoot in this sample)
    median, and the absolute wall_ms those correspond to

Plus `movetime_minus_overhead`, the limit the engine actually arms: the movetime
path sets hard = max(1, movetime - MoveOverhead) with soft = hard
(src/search.cpp:2192-2193). That is a prediction the measurement can refute.

Runs on several positions so a single position's depth-1 cost cannot set the
floor for every request.
"""
from __future__ import annotations

import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucilib import Engine  # noqa: E402

POSITIONS = {
    "opening": "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
    "midgame": "r2q1rk1/pp1n1ppp/2pbpn2/3p4/2PP4/1PN1PN2/PB2BPPP/R2Q1RK1 w - - 0 10",
    "endgame": "8/2p2ppk/1p2b2p/p7/P1P1P3/1P3P1P/3R2K1/8 w - - 0 30",
    "bare": "8/8/8/4k3/8/8/4K3/7R w - - 0 40",
}
REQUESTS = [10, 50, 100, 500, 2000]
REPS = 15


def main():
    exe, outpath = sys.argv[1], sys.argv[2]
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    ovh = 10
    e = Engine(exe)
    e.set_option("OwnBook", "false")
    e.set_option("Threads", "1")

    rows = []
    for pname, fen in POSITIONS.items():
        e.send(f"position fen {fen}")
        # warm-up, discarded: first search on a fresh TT is not the same object
        e.go("movetime 100", timeout=10.0)
        for req in REQUESTS:
            walls = []
            depths = []
            for _ in range(REPS):
                e.send(f"position fen {fen}")
                r = e.go(f"movetime {req}", timeout=max(10.0, req / 1000.0 + 15.0))
                if r.timed_out:
                    walls.append(float("inf"))
                    continue
                walls.append(r.wall_ms)
                depths.append(r.depth_reached)
            good = [w for w in walls if w != float("inf")]
            if not good:
                rows.append({"position": pname, "requested": req, "timed_out_all": True})
                continue
            armed = max(1, req - ovh)
            rows.append({
                "position": pname,
                "requested": req,
                "armed_limit_ms": armed,
                "n": len(good),
                "n_timeout": len(walls) - len(good),
                "floor_ms": round(min(good), 3),
                "median_ms": round(statistics.median(good), 3),
                "ceiling_ms": round(max(good), 3),
                "floor_ratio": round(min(good) / req, 4),
                "median_ratio": round(statistics.median(good) / req, 4),
                "ceiling_ratio": round(max(good) / req, 4),
                "median_depth": statistics.median(depths) if depths else None,
            })
            r_ = rows[-1]
            print(f"{pname:<8} req={req:>5} armed={armed:>5} "
                  f"floor={r_['floor_ms']:>8.2f}({r_['floor_ratio']:.3f}) "
                  f"med={r_['median_ms']:>8.2f}({r_['median_ratio']:.3f}) "
                  f"ceil={r_['ceiling_ms']:>8.2f}({r_['ceiling_ratio']:.3f}) "
                  f"n={r_['n']} to={r_['n_timeout']}", flush=True)
    e.close()

    # Aggregate across positions, per request: the floor is a property of the
    # request, so the global floor is the min over positions and the global
    # ceiling the max.
    agg = []
    for req in REQUESTS:
        sub = [r for r in rows if r.get("requested") == req and not r.get("timed_out_all")]
        if not sub:
            continue
        floors = [r["floor_ms"] for r in sub]
        meds = [r["median_ms"] for r in sub]
        ceils = [r["ceiling_ms"] for r in sub]
        agg.append({
            "requested": req,
            "armed_limit_ms": max(1, req - ovh),
            "floor_ms": round(min(floors), 3),
            "floor_ratio": round(min(floors) / req, 4),
            "median_ms": round(statistics.median(meds), 3),
            "median_ratio": round(statistics.median(meds) / req, 4),
            "ceiling_ms": round(max(ceils), 3),
            "ceiling_ratio": round(max(ceils) / req, 4),
            "positions": len(sub),
        })
    with open(outpath, "w") as f:
        json.dump({"exe": exe, "overhead": ovh, "reps": REPS, "per_position": rows, "aggregate": agg}, f, indent=2)
    print("\nAGGREGATE (floor = min over positions, ceiling = max)")
    for a in agg:
        print(f"req={a['requested']:>5} armed={a['armed_limit_ms']:>5} "
              f"floor={a['floor_ms']:>8.2f} ({a['floor_ratio']:.3f}x)  "
              f"med={a['median_ms']:>8.2f} ({a['median_ratio']:.3f}x)  "
              f"ceil={a['ceiling_ms']:>8.2f} ({a['ceiling_ratio']:.3f}x)")
    print("wrote", outpath)


if __name__ == "__main__":
    main()
