#!/usr/bin/env python3
"""Classify the M > N cells and separate two things the count conflates.

A cell where `go mate N` reports `mate M` with M > N is not automatically wrong.
The qsearch clamp lets the search see a few plies beyond 2N-1, so it can find a
mate that genuinely needs more than N moves and report it CORRECTLY. That is a
mislabelled promise ("go mate 3" answering mate 4) but not a false claim.

Two classes, and only the second is a defect:

  A. FOUND FURTHER, AND RIGHT  — reported distance == oracle distance, but > N.
     The report is true; the REQUEST was not honoured as advertised.
  B. WRONG DISTANCE            — reported distance != oracle distance. The PV
     does not replay to mate either. This is a false claim.

Plus a control the whole classification rests on: for every one of these boards,
the SAME request at the truth's own N must report the truth. If it does not, the
error is not edge-local and the classification above is the wrong frame.

Usage: classify_overclaims.py --exe build/forge --out overclaim_classified.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucipipe import Engine  # noqa: E402
from mateoracle import Oracle, pv_replays_to_mate  # noqa: E402


def ask(exe: str, fen: str, n: int) -> dict:
    with Engine(exe, {"OwnBook": "false"}) as eng:
        eng.newgame()
        eng.setpos(fen)
        res = eng.go(f"go mate {n}", timeout=900)
    sc = res.last_score or (None, None)
    return {"n": n, "kind": sc[0], "value": sc[1], "depth": res.last_depth,
            "nodes": res.last_nodes, "bestmove": res.bestmove,
            "pv": res.last_pv, "pv_len": len(res.last_pv)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", default="build/forge")
    ap.add_argument("--hits", default="evidence/overclaim_scan.json")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    data = json.load(open(args.hits))
    rows = []
    for h in data["hits"]:
        board = chess.Board(h["fen"])
        o = Oracle(node_budget=40_000_000)
        exact = o.exact_dtm_up_to(board, 8)
        truth_moves = (exact + 1) // 2 if exact else None
        reported = h["reported_mate"]
        replay_ok, replay_detail = pv_replays_to_mate(board, h["pv"])
        cls = ("B_WRONG_DISTANCE" if truth_moves is not None and reported != truth_moves
               else "A_FOUND_FURTHER_AND_RIGHT" if reported > h["n"]
               else "C_within_N")
        # Control: the same board at the truth's own N.
        control = ask(args.exe, h["fen"], truth_moves) if truth_moves else None
        control_ok = (control is not None and control["kind"] == "mate"
                      and control["value"] == truth_moves)
        row = {
            "fen": h["fen"], "material": h["material"], "requested_n": h["n"],
            "reported_mate": reported, "true_moves": truth_moves,
            "true_plies": exact, "class": cls,
            "pv_len": h["pv_len"], "implied_plies": 2 * reported - 1,
            "pv_replays_to_mate": replay_ok, "pv_detail": replay_detail,
            "control_at_true_n": control, "control_reports_truth": control_ok,
            "nodes": h["nodes"], "bestmove": h["bestmove"],
        }
        rows.append(row)
        print(f"{cls:26s} {h['material']:8s} go mate {h['n']} -> mate {reported} "
              f"(truth {truth_moves}, PV {h['pv_len']} plies, replays={replay_ok}); "
              f"control at N={truth_moves}: "
              f"{control['kind']}{control['value'] if control else '-'} ok={control_ok}")

    a = [r for r in rows if r["class"].startswith("A_")]
    b = [r for r in rows if r["class"].startswith("B_")]
    print(f"\nclass A (correct distance, beyond N): {len(a)}")
    print(f"class B (WRONG distance): {len(b)}")
    print(f"controls that report the truth at the truth's own N: "
          f"{sum(1 for r in rows if r['control_reports_truth'])}/{len(rows)}")

    json.dump({"rows": rows,
               "counts": {"A": len(a), "B": len(b), "total": len(rows)},
               "controls_ok": sum(1 for r in rows if r["control_reports_truth"])},
              open(args.out, "w"), indent=1)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
