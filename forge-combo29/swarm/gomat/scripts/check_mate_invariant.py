#!/usr/bin/env python3
"""Check the one invariant that makes a mate score falsifiable without a solver.

A mate score of `mate M` asserts a forced mate in `2M-1` plies. A search that
reaches `sd` plies cannot PROVE a mate longer than `sd` plies. So for every
`info ... score mate M ... seldepth sd` line, the implied distance must satisfy

       2M - 1  <=  sd          (+ the qsearch horizon, which is bounded by sd)

This is checked against the SELDEPTH the engine reports, and separately against
the LENGTH OF ITS OWN PV. A score whose implied distance exceeds its PV length is
internally inconsistent: the engine is claiming a mate one or more moves beyond
the line it can actually show.

This is a check on the engine's self-consistency, not on its correctness — a
mate claim can pass it and still be the wrong distance, which is why every
positive claim is also replayed in python-chess elsewhere. Stated here so the
limit travels with the number.

Usage: check_mate_invariant.py --dir evidence --out mate_invariant.json
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mateoracle import pv_replays_to_mate  # noqa: E402

def implied_plies(mate_moves: int) -> int:
    """A `score mate M` token means M MOVES, i.e. 2M-1 plies for the attacker.

    The value arriving here is the parsed distance in moves, not the raw
    centipawn-encoded score. The first version of this function subtracted it
    from MateValue, which turned `mate 3` into 31,997 plies and produced 20
    false alarms; findings §6's "a check that fires on correct usage is worse
    than none" is exactly this failure, and it was caught by reading the output
    rather than by the check itself.
    """
    return 2 * abs(mate_moves) - 1


def check_cell(fen: str, cell: dict, label: str) -> dict | None:
    kind = cell.get("score_kind")
    val = cell.get("score_value")
    if kind != "mate" or val is None or val == 0:
        return None
    plies = implied_plies(val)
    pv = cell.get("pv") or []
    seldepth = cell.get("seldepth")
    depth = cell.get("depth")
    rec = {
        "label": label, "fen": fen, "mate": val, "implied_plies": plies,
        "pv_len": len(pv), "depth": depth, "seldepth": seldepth,
        "bestmove": cell.get("bestmove"),
        "plies_exceed_pv": plies > len(pv),
        "plies_exceed_seldepth": (plies > seldepth) if seldepth else None,
        "plies_exceed_depth": (plies > depth) if depth else None,
    }
    if val > 0:
        ok, detail = pv_replays_to_mate(chess.Board(fen), pv)
        rec["pv_replays_to_mate"] = ok
        rec["pv_detail"] = detail
    else:
        rec["pv_replays_to_mate"] = None
        rec["pv_detail"] = "negative mate: the defender's loss"
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="evidence")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    found: list[dict] = []
    scanned = 0

    for name in ("raw_modes.json", "compare_real.json", "compare_mate.json"):
        path = os.path.join(args.dir, name)
        if not os.path.exists(path):
            continue
        data = json.load(open(path))
        for row in data:
            fen = row.get("fen")
            if "searches" in row:                       # raw_modes shape
                for key, cell in row["searches"].items():
                    scanned += 1
                    rec = check_cell(fen, cell, f"{row['id']}|{key}")
                    if rec:
                        found.append(rec)
            else:                                       # compare_* shape
                for mode in ("mate", "depth"):
                    scanned += 1
                    rec = check_cell(fen, row[mode], f"{row['id']}|{mode}|N{row['N']}")
                    if rec:
                        found.append(rec)

    for name in ("surface.json", "edges.json", "overclaim.json", "termination_a.json"):
        path = os.path.join(args.dir, name)
        if not os.path.exists(path):
            continue
        data = json.load(open(path))
        stack = [data]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                if "score_kind" in node and "fen" in node:
                    scanned += 1
                    cell = {"score_kind": node.get("score_kind"),
                            "score_value": node.get("score_value"),
                            "pv": node.get("pv", []),
                            "depth": node.get("depth"),
                            "seldepth": node.get("seldepth"),
                            "bestmove": node.get("bestmove")}
                    rec = check_cell(node["fen"], cell, f"{name}|{node.get('n', node.get('cmd', '?'))}")
                    if rec:
                        found.append(rec)
                for v in node.values():
                    if isinstance(v, (dict, list)):
                        stack.append(v)
            elif isinstance(node, list):
                stack.extend(node)

    print(f"scanned {scanned} scored cells; {len(found)} carried a non-zero mate score\n")
    bad_pv = [r for r in found if r["plies_exceed_pv"]]
    bad_sd = [r for r in found if r["plies_exceed_seldepth"]]
    bad_replay = [r for r in found if r["pv_replays_to_mate"] is False]

    print(f"mate scores whose implied plies EXCEED their own PV length: {len(bad_pv)}")
    for r in bad_pv:
        print(f"  {r['label']:34s} mate {r['mate']:+d} implies {r['implied_plies']} plies, "
              f"PV {r['pv_len']} plies, depth {r['depth']}, seldepth {r['seldepth']}  "
              f"replay={r['pv_replays_to_mate']}")
    print(f"\nmate scores whose implied plies EXCEED seldepth: {len(bad_sd)}")
    for r in bad_sd:
        print(f"  {r['label']:34s} mate {r['mate']:+d} implies {r['implied_plies']}, seldepth {r['seldepth']}")
    print(f"\nPOSITIVE mate scores whose PV does not replay to mate: {len(bad_replay)}")
    for r in bad_replay:
        print(f"  {r['label']:34s} mate {r['mate']:+d}: {r['pv_detail']}")

    json.dump({"scanned": scanned, "mate_cells": found,
               "plies_exceed_pv": bad_pv, "plies_exceed_seldepth": bad_sd,
               "pv_replay_failures": bad_replay}, open(args.out, "w"), indent=1)
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
