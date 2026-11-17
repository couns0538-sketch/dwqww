#!/usr/bin/env python3
"""Attribute the mate-distance overclaim to a gate, by running it across arms.

The overclaim (see run_overclaim.py): `go mate 4` on a proved mate-in-5 reports
`mate 6` with a 7-ply PV that does not reach mate, while `go mate 5` gets it
right. This script runs the SAME six requests on every ablation arm, so the
question "which disabled heuristic causes the wrong distance" is answered by a
table rather than by reading the code.

Two candidate mechanisms, and they make OPPOSITE predictions, which is why this
is a measurement and not a guess:

  * the WINDOW (search.cpp:1431 / 1572) — the mate window clamps beta to
    mate_in(ply+1) at every node, so removing it should change the distance;
  * the TT cutoff — in mate mode a TT cut is allowed only when alpha/beta are
    ALREADY mate scores, which the narrow window makes common. Enabling the TT
    gates makes cutoffs MORE permissive, so if the TT is the cause the distance
    should get WORSE, not better.

Usage: run_overclaim_arms.py --dir /tmp/ab --out overclaim_arms.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucipipe import Engine  # noqa: E402
from mateoracle import Oracle  # noqa: E402

FEN = "8/7Q/8/8/K7/8/8/5k2 w - - 0 1"
TRUE_MOVES = 5


def arm_answers(exe: str) -> list[dict]:
    out = []
    for n in (1, 2, 3, 4, 5, 6):
        with Engine(exe, {"OwnBook": "false"}) as eng:
            eng.newgame()
            eng.setpos(FEN)
            res = eng.go(f"go mate {n}", timeout=600)
        sc = res.last_score or (None, None)
        out.append({
            "n": n, "score_kind": sc[0], "score_value": sc[1],
            "depth": res.last_depth, "nodes": res.last_nodes,
            "bestmove": res.bestmove, "pv_len": len(res.last_pv),
            "distance_error": (sc[1] - TRUE_MOVES) if sc[0] == "mate" else None,
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="/tmp/ab")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    board = chess.Board(FEN)
    exact = Oracle(node_budget=30_000_000).exact_dtm_up_to(board, 6)
    true_moves = (exact + 1) // 2
    print(f"{FEN}\noracle exact DTM {exact} plies = {true_moves} moves\n")

    builds = []
    with open(os.path.join(args.dir, "BUILDS.txt")) as fh:
        next(fh)
        for line in fh:
            name, gates, digest = line.rstrip("\n").split("\t")
            builds.append((name, gates, digest))

    header = (f"{'arm':28s} " + " ".join(f"{'mate' + str(n):>9s}" for n in range(1, 7))
              + "   overclaims")
    print(header)
    print("-" * len(header))
    rows = []
    for name, gates, _ in builds:
        exe = os.path.join(args.dir, name, "build", "forge")
        try:
            ans = arm_answers(exe)
        except Exception as exc:                       # noqa: BLE001
            print(f"{name:28s} ERROR {exc}")
            continue
        cells = []
        for a in ans:
            if a["score_kind"] == "mate":
                cells.append(f"m{a['score_value']:+d}")
            else:
                cells.append(f"cp{a['score_value']}" if a["score_value"] is not None else "-")
        over = sum(1 for a in ans if a["score_kind"] == "mate" and a["score_value"] > a["n"])
        print(f"{name:28s} " + " ".join(f"{c:>9s}" for c in cells) + f"   {over}")
        rows.append({"arm": name, "gates": gates, "answers": ans, "overclaims": over})

    json.dump({"fen": FEN, "oracle_dtm_plies": exact, "true_moves": true_moves,
               "arms": rows}, open(args.out, "w"), indent=1)
    print(f"\nwrote {args.out}")
    base = next(r for r in rows if r["arm"] == "control")
    changed = [r["arm"] for r in rows
               if [a["score_value"] for a in r["answers"]] != [a["score_value"] for a in base["answers"]]]
    print(f"\narms whose six answers differ from the control: {len(changed)}")
    for a in changed:
        print(f"  {a}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
