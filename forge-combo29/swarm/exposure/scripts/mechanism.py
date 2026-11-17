#!/usr/bin/env python3
"""Verify the bail's MECHANISM on every measured row: does it play the head of the
engine's own generated move list?

The report asserts this on six constructed fixtures ("the bail returns the head of
the generated list"). It is cheap to check on real roots, and if it fails anywhere the
mechanism claim is narrower than it reads. `go perft 1` prints the engine's legal moves
in ITS generation order, one `move: 1` line each, so the head is read from the binary
rather than from python-chess -- whose order differs (it sorts by square, the engine
by piece and offset).

Also checks the base's move against the engine's full perft-1 list (legality gate).
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import subprocess
import sys

# Evidence root: override with FORGE_EXPOSURE_ROOT. Defaults to the parent of scripts/.
ROOT = os.environ.get("FORGE_EXPOSURE_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BUILD = os.path.join(ROOT, "build-base", "forge")


def perft1(fen: str) -> list[str]:
    script = f"uci\nisready\nposition fen {fen}\ngo perft 1\nquit\n"
    out = subprocess.run([BUILD], input=script, capture_output=True,
                         text=True, timeout=120).stdout
    moves = []
    for line in out.splitlines():
        # `b7a6: 1` -- a legal move and its leaf count.
        if ": " in line and len(line.split()) == 2:
            head = line.split(":")[0]
            if 4 <= len(head) <= 5 and head[0] in "abcdefgh":
                moves.append(head)
    return moves


def check(row: dict) -> dict:
    moves = perft1(row["fen"])
    head = moves[0] if moves else None
    return {
        "fen": row["fen"],
        "reason": row["reason"],
        "halfmove": row["halfmove"],
        "base_move": row["move_base"],
        "generated_head": head,
        "n_generated": len(moves),
        "is_head": row["move_base"] == head,
        "in_generated": row["move_base"] in moves,
        "py_first_legal": row.get("py_first_legal"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cost", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--jobs", type=int, default=os.cpu_count())
    args = ap.parse_args()
    d = json.load(open(args.cost))
    rows = [r for r in d["rows"] if "error" not in r]
    with mp.Pool(args.jobs) as pool:
        res = pool.map(check, rows, chunksize=1)
    head = sum(r["is_head"] for r in res)
    inside = sum(r["in_generated"] for r in res)
    print(f"{len(res)} rows: base move is the generated HEAD {head}/{len(res)}; "
          f"legal in the engine's own list {inside}/{len(res)}")
    bad = [r for r in res if not r["is_head"]]
    for r in bad[:10]:
        print(f"  NOT HEAD: {r['fen']} base={r['base_move']} head={r['generated_head']}")
    with open(args.out, "w") as fh:
        json.dump({"rows": res, "is_head": head, "in_generated": inside}, fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
