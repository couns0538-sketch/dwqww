#!/usr/bin/env python3
"""Last-wins asymmetry: a repeated keyword where the SECOND value is malformed.

`nodes` sets its field only when the parse succeeds, so a bad second value leaves
the first budget standing. `depth` goes through `read_int`, which returns 0 on
failure and is then clamped to 1, so a bad second value REPLACES a good first
one. Both are "the same keyword twice"; only one of them keeps your limit.

Also checks whether a zero is the same hazard as a malformed value on the
keywords where 0 is legal.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from go_probe import MIDGAME_WHITE, run_cell, verdict  # noqa: E402

BUILD = "base@6b98f217 (g++ 13.3.0, sha256 e06310ec)"

CELLS = [
    ("repeat: good nodes then junk", "go nodes 50000 nodes abc", "does the 50k budget survive?"),
    ("repeat: good nodes then 0", "go nodes 50000 nodes 0", "does an explicit 0 survive it?"),
    ("repeat: good depth then junk", "go depth 8 depth abc", "does depth 8 survive?"),
    ("repeat: good depth then 0", "go depth 8 depth 0", "does depth 8 survive?"),
    ("repeat: good wtime then junk", "go wtime 2000 wtime abc", "clock set twice"),
    ("repeat: good movetime then junk", "go movetime 200 movetime abc", "movetime set twice"),
    ("repeat: good mate then junk", "go mate 2 mate abc", "mate set twice"),
    # Controls, one instance each.
    ("control: nodes 50000", "go nodes 50000", "reference"),
    ("control: depth 8", "go depth 8", "reference"),
    ("control: wtime 2000", "go wtime 2000", "reference"),
    ("control: movetime 200", "go movetime 200", "reference"),
    ("control: mate 2", "go mate 2", "reference"),
]


def main() -> int:
    exe = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/build/base/forge"
    rows = []
    for form, command, note in CELLS:
        c = run_cell(exe, command, MIDGAME_WHITE, False, 20.0, build=BUILD)
        row = c.as_dict()
        row.update({"verdict": verdict(c), "note": note, "form": form, "keyword": "last-wins", "section": "lastwins"})
        rows.append(row)
        print(
            f'{verdict(c):18s} d={c.max_depth} n={c.last_nodes} bm={c.bestmove} L={c.info_depth_lines} '
            f'stop->{c.stop_bestmove} | {command}',
            flush=True,
        )
    out = Path(__file__).resolve().parent.parent / "evidence"
    with (out / "lastwins.jsonl").open("w") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
