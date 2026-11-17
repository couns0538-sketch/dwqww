#!/usr/bin/env python3
"""What a clock does to the LABEL, not just to the time.

Findings §7 3aa already records that "a depth column measured under a timeout is
a column of the harness's patience". This asks a narrower and more damaging
question about `go mate N`: when a clock aborts an iteration, which score is
published against which depth?

`search.cpp` publishes, on abort and only when the partial PV's first move
differs from the last finished PV's first move:

    emit(depth, result.score, result.pv)

where `depth` is the UNFINISHED iteration's depth and `result.score` is the LAST
FINISHED iteration's score. So the line a consumer reads can carry a depth it
never completed and a score from a shallower search, with a PV from the
unfinished one. This script measures whether that happens on `go mate N`.

Method: run the same board at a ladder of movetimes. For each, take the LAST
info line and compare its score to the score the engine reports at the SAME
reported depth with NO clock. If they differ, the label is mixed.

Usage: run_clock_label.py --exe build/forge --out clock_label.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucipipe import Engine  # noqa: E402

BOARDS = [
    ("mate-in-4", "8/8/4R3/8/3R4/8/2k3K1/8 w - - 0 1"),
    ("startpos", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
    ("kiwipete", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"),
]
MOVETIMES = [5, 10, 20, 40, 80, 160, 320]


def all_info(exe: str, fen: str, cmd: str) -> dict:
    with Engine(exe, {"OwnBook": "false"}) as eng:
        eng.newgame()
        eng.setpos(fen)
        res = eng.go(cmd, timeout=900)
    per_depth = {}
    for ln in res.info_depths:
        tok = ln.split()
        try:
            d = int(tok[tok.index("depth") + 1])
            sd = int(tok[tok.index("seldepth") + 1])
        except (ValueError, IndexError):
            continue
        kind = tok[tok.index("score") + 1]
        val = int(tok[tok.index("score") + 2])
        nodes = int(tok[tok.index("nodes") + 1]) if "nodes" in tok else None
        pv = tok[tok.index("pv") + 1:] if "pv" in tok else []
        per_depth[d] = {"seldepth": sd, "score": [kind, val], "nodes": nodes,
                        "pv": pv, "pv_len": len(pv)}
    return {"per_depth": per_depth, "last": res.last_score, "last_depth": res.last_depth,
            "bestmove": res.bestmove, "wall_s": round(res.wall_s, 4),
            "timed_out": res.timed_out, "lines": res.info_depths}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", default="build/forge")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    out = []
    for name, fen in BOARDS:
        ref = all_info(args.exe, fen, "go mate 4")
        print(f"\n=== {name}: reference go mate 4, no clock")
        for d, v in sorted(ref["per_depth"].items()):
            print(f"  depth {d:2d} seldepth {v['seldepth']:2d} {str(v['score']):14s} "
                  f"nodes {v['nodes']:>10} pvlen {v['pv_len']}")
        # The reference score at each depth, for comparison.
        ref_by_depth = {d: v["score"] for d, v in ref["per_depth"].items()}

        for mt in MOVETIMES:
            got = all_info(args.exe, fen, f"go mate 4 movetime {mt}")
            last = got["last"]
            ld = got["last_depth"]
            want = ref_by_depth.get(ld)
            want_norm = list(want) if want is not None else None
            last_norm = list(last) if last is not None else None
            v = got["per_depth"].get(ld, {})
            # Compare NORMALISED forms: the tuple coming out of the parser and
            # the list built from the info line are the same score. The first
            # version compared them raw and reported 21 of 21 cells "mixed",
            # which is a type mismatch wearing a finding's clothes.
            mixed = want is not None and last_norm != want_norm
            rec = {
                "board": name, "fen": fen, "movetime": mt,
                "last_depth": ld, "last_score": last, "reference_at_that_depth": want,
                "seldepth": v.get("seldepth"), "nodes": v.get("nodes"),
                "pv_len": v.get("pv_len"), "bestmove": got["bestmove"],
                "wall_s": got["wall_s"], "score_mixed_with_depth": mixed,
            }
            out.append(rec)
            flag = "  <-- SCORE NOT THE ONE THE REFERENCE GIVES AT THIS DEPTH" if mixed else ""
            print(f"  movetime {mt:4d}ms -> depth {ld} {str(last):14s} "
                  f"ref@d{ld}={want} nodes {v.get('nodes')} pvlen {v.get('pv_len')} "
                  f"wall {got['wall_s']:.3f}{flag}", flush=True)

    json.dump(out, open(args.out, "w"), indent=1)
    bad = [r for r in out if r["score_mixed_with_depth"]]
    print("\ncells where a clocked mate search published a score that the "
          f"no-clock search does not give at the same reported depth: {len(bad)}/{len(out)}")
    for r in bad:
        print(f"  {r['board']:12s} movetime {r['movetime']:4d}ms depth {r['last_depth']} "
              f"reported {r['last_score']} vs reference {r['reference_at_that_depth']}")
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
