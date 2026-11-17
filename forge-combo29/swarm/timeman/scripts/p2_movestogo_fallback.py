#!/usr/bin/env python3
"""P2: the recorded gap — `movestogo` meeting the FALLBACK clock (trap 19e).

The question is not "what does movestogo mean" (measured elsewhere). It is:
with White to move and only `btime` sent, the budget comes from the OPPONENT's
clock. When parse_limits resolves that fallback, does movestogo still reach the
planner, does the planner take the movestogo branch, and does the >50 clamp apply?

Three arms:
  A  own clock + movestogo        (the branch that already worked)
  B  OPPONENT clock + movestogo   (the fallback branch: base does not even return)
  C  OPPONENT clock, no movestogo (fallback without movestogo, the 19e case)

Predictions are computed from the engine's own clock_plan.hpp via plan_table.cpp,
so every row carries the exact soft/hard the planner should produce.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucilib import Engine, plan_clock  # noqa: E402

FEN_W = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
FEN_B = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 4 4"
OVH = 10


def run(exe, fen, spec, timeout, label, mtg_raw=None, clock_ms=None):
    e = Engine(exe)
    e.set_option("OwnBook", "false")
    e.send(f"position fen {fen}")
    r = e.go(spec, timeout=timeout)
    e.close()
    parsed = None if mtg_raw is None else max(1, mtg_raw)
    soft = hard = None
    if clock_ms is not None:
        soft, hard, _ = plan_clock(clock_ms, 0, parsed if parsed is not None else 0, OVH)
    return {
        "label": label,
        "spec": "go " + spec,
        "wall_ms": round(r.wall_ms, 2),
        "bestmove": r.bestmove,
        "timed_out": r.timed_out,
        "depth": r.depth_reached,
        "nodes": r.nodes,
        "info_count": len(r.info_lines),
        "mtg_token": mtg_raw,
        "mtg_parsed": parsed,
        "resolved_clock_ms": clock_ms,
        "plan_soft_ms": soft,
        "plan_hard_ms": hard,
    }


def main():
    exe, outdir, tag = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(outdir, exist_ok=True)
    rows = []
    T = 12.0

    # Control: the plan on a both-clocks form with no movestogo, so wall times
    # below have something on the same binary to be compared against.
    rows.append(run(exe, FEN_W, "wtime 2000 btime 2000", T, "C both clocks, no movestogo", None, 2000))

    for raw in [1, 2, 20, 50, 100]:
        # A: own clock
        rows.append(run(exe, FEN_W, f"wtime 2000 btime 2000 movestogo {raw}", T,
                        f"A own clock + movestogo {raw}", raw, 2000))
    for raw in [1, 2, 20, 50, 100]:
        # B: OPPONENT clock only + movestogo  <-- the recorded gap
        rows.append(run(exe, FEN_W, f"btime 2000 movestogo {raw}", T,
                        f"B opponent clock + movestogo {raw}", raw, 2000))
    for raw in [0, -1]:
        rows.append(run(exe, FEN_W, f"btime 2000 movestogo {raw}", T,
                        f"B opponent clock + movestogo {raw}", raw, 2000))
        rows.append(run(exe, FEN_W, f"wtime 2000 btime 2000 movestogo {raw}", T,
                        f"A own clock + movestogo {raw}", raw, 2000))
    # C: fallback, no movestogo
    rows.append(run(exe, FEN_W, "btime 2000", T, "C opponent clock, no movestogo", None, 2000))
    # Mirror side: Black to move with only wtime (the other fallback direction)
    rows.append(run(exe, FEN_B, "wtime 2000 movestogo 20", T,
                    "B' black to move, only wtime + movestogo 20", 20, 2000))
    rows.append(run(exe, FEN_B, "btime 2000 movestogo 20", T,
                    "A' black to move, own clock + movestogo 20", 20, 2000))

    out = os.path.join(outdir, f"p2_movestogo_fallback_{tag}.json")
    with open(out, "w") as f:
        json.dump({"exe": exe, "tag": tag, "fen_white": FEN_W, "fen_black": FEN_B, "rows": rows}, f, indent=2)
    for r in rows:
        print(f"{r['label']:<46} wall={r['wall_ms']:>9.2f}ms to={str(r['timed_out']):<5} "
              f"depth={r['depth']:>3} plan={r['plan_soft_ms']}/{r['plan_hard_ms']} bm={r['bestmove']}")
    print("json:", out)


if __name__ == "__main__":
    main()
