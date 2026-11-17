#!/usr/bin/env python3
"""Re-run of the searchmoves cells with a move that is actually legal there.

The first pass used `e2e4` as the "valid" control, which is illegal on the
midgame board (the e-pawn is already on e4), so all eight cells returned the
all-illegal path. That is a harness error, not an engine result, and it is kept
in the record rather than quietly overwritten: the first pass is in
`keywords.jsonl` (rows 70-75 show the same signature), this file is the
corrected pass. `d2d4` is legal there (perft 1 lists it).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from go_probe import MIDGAME_WHITE, run_cell, verdict  # noqa: E402

BUILD = "base@6b98f217 (g++ 13.3.0, sha256 e06310ec)"

CELLS = [
    ("searchmoves", "no moves", "go searchmoves", "specified but empty"),
    ("searchmoves", "junk", "go searchmoves abc", "not a move"),
    ("searchmoves", "illegal move", "go searchmoves a7a8", "legal-format illegal move"),
    ("searchmoves", "valid", "go searchmoves d2d4", "LEGAL move, no other limit"),
    ("searchmoves", "valid+limit", "go searchmoves d2d4 depth 8", "legal move + depth"),
    ("searchmoves", "mixed", "go searchmoves d2d4 a7a8", "one legal, one illegal"),
    ("searchmoves", "junk+limit", "go searchmoves abc depth 8", "junk move + depth"),
    ("searchmoves", "two legal", "go searchmoves d2d4 e1g1 depth 4", "two legal moves"),
    ("searchmoves", "valid+clock", "go searchmoves d2d4 wtime 1000", "legal move + clock"),
    ("searchmoves", "valid+bad nodes", "go searchmoves d2d4 nodes abc", "legal move, unbounded?"),
    ("searchmoves", "valid no limit", "go searchmoves d2d4", "legal move, no limit at all"),
]


def main() -> int:
    exe = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/build/base/forge"
    rows = []
    for keyword, form, command, note in CELLS:
        c = run_cell(exe, command, MIDGAME_WHITE, False, 20.0, build=BUILD)
        row = c.as_dict()
        row.update({"verdict": verdict(c), "note": note, "form": form, "keyword": keyword, "section": "searchmoves"})
        rows.append(row)
        print(
            f'{verdict(c):18s} d={c.max_depth} n={c.last_nodes} bm={c.bestmove} L={c.info_depth_lines} '
            f'stop->{c.stop_bestmove} | {command}',
            flush=True,
        )
    out = Path(__file__).resolve().parent.parent / "evidence"
    with (out / "searchmoves.jsonl").open("w") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
