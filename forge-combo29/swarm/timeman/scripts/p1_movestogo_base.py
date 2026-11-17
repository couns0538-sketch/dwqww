#!/usr/bin/env python3
"""P1: what the base commit does with movestogo, and with a one-sided clock.

Every probe here turns OwnBook off. Trap 19 says the book fires on a clock
search, and trap 19e records that a seat's first "fixed" measurement was the
book short-circuit returning before the time manager was ever consulted. With
OwnBook true these probes would measure the book.

Also prints the Python mirror of clock_plan.hpp beside each wall time so a
disagreement is visible in the artefact.

Usage: p1_movestogo_base.py <exe> <outdir>
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucilib import Engine, plan_clock  # noqa: E402

# A quiet opening position with no book dependence, White to move.
FEN_W = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
FEN_W_MOVENUM = FEN_W
FEN_B = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 4 4"

OVERHEAD = 10


def one(exe, fen, spec, timeout, label, movetime=None):
    e = Engine(exe)
    e.set_option("OwnBook", "false")
    e.send(f"position fen {fen}")
    r = e.go(spec, timeout=timeout)
    e.close()
    return {
        "label": label,
        "spec": "go " + spec,
        "side": "white" if " w " in fen else "black",
        "wall_ms": round(r.wall_ms, 2),
        "bestmove": r.bestmove,
        "timed_out": r.timed_out,
        "depth": r.depth_reached,
        "nodes": r.nodes,
        "info_count": len(r.info_lines),
    }


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    rows = []

    # --- 1. movestogo clamp: 0, 1, -1, 50, 100, absent, at a 2000 ms clock ---
    for mtg in ["0", "1", "-1", "50", "100", "absent"]:
        spec = "wtime 2000 btime 2000" if mtg == "absent" else \
               f"wtime 2000 btime 2000 movestogo {mtg}"
        # parse_limits does std::max(1, read_int()); model that here so the
        # mirror states the engine's own transform rather than the raw token.
        raw = None if mtg == "absent" else int(mtg)
        parsed = None if raw is None else max(1, raw)
        pred = plan_clock(2000, 0, parsed if parsed is not None else 0, OVERHEAD)
        row = one(exe, FEN_W, spec, timeout=8.0, label=f"mtg={mtg}")
        row["token"] = mtg
        row["parsed_moves_to_go"] = parsed
        row["mirror_soft_ms"] = pred[0]
        row["mirror_hard_ms"] = pred[1]
        rows.append(row)

    # --- 2. one-sided clock on the base commit (trap 18/19): does it return? ---
    for spec, lab in [
        ("btime 10000", "white to move, OPPONENT clock only"),
        ("wtime 10000", "white to move, own clock only"),
        ("wtime 10000 btime 10000", "white to move, both clocks"),
        (f"btime 10000 movestogo 20", "white to move, OPPONENT clock + movestogo 20"),
        (f"wtime 10000 movestogo 20", "white to move, own clock + movestogo 20"),
    ]:
        row = one(exe, FEN_W, spec, timeout=12.0, label=lab)
        rows.append(row)

    # --- 3. movestogo with no clock at all: recorded unbounded, rechecked here
    # only so the same binary is on record; not reported as new. ---
    row = one(exe, FEN_W, "movestogo 20", timeout=6.0, label="movestogo 20, no clock")
    rows.append(row)

    out = os.path.join(outdir, "p1_movestogo_base.json")
    with open(out, "w") as f:
        json.dump({"exe": exe, "fen_white": FEN_W, "overhead": OVERHEAD, "rows": rows}, f, indent=2)

    for r in rows:
        print(f"{r['label']:<52} wall={r['wall_ms']:>9.2f}ms depth={r['depth']:>3} "
              f"to={str(r['timed_out']):<5} bm={r['bestmove']} "
              f"mirror={r.get('mirror_soft_ms', '-')}/{r.get('mirror_hard_ms', '-')}")
    print("json:", out)


if __name__ == "__main__":
    main()
