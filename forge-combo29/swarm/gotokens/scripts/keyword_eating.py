#!/usr/bin/env python3
"""Keyword-eating: a keyword with no value CONSUMES the next keyword as its value.

`read_int`, `read_clock` and the `nodes` branch each advance the token index
before deciding the token was not a number. So in `go nodes depth 5` the
`nodes` branch eats the literal token `depth` as its value, fails to parse it,
sets no node limit, and then `5` is a stray token that matches no keyword. The
result is a search with NO LIMIT AT ALL, even though the caller wrote a
perfectly good `depth 5`.

This is the sharpest form of the combination question, and it is not reachable
from a per-keyword matrix: every individual token is well-formed. It is only
visible when a malformed keyword sits immediately before a good one.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from go_probe import MIDGAME_WHITE, run_cell, verdict  # noqa: E402

BUILD = "base@6b98f217 (g++ 13.3.0, sha256 e06310ec)"

CELLS = [
    # The claim: the value-less keyword swallows the NEXT KEYWORD.
    ("nodes eats depth", "go nodes depth 5", "if depth binds -> it did not get eaten"),
    ("depth eats nodes", "go depth nodes 50000", "depth takes 'nodes' as its value -> 1 ply"),
    ("wtime eats depth", "go wtime depth 5", "wtime takes 'depth' -> 0 ms clock"),
    ("movetime eats depth", "go movetime depth 5", "movetime takes 'depth' -> 0 ms"),
    ("mate eats depth", "go mate depth 5", "mate takes 'depth' -> 0 -> unbounded"),
    ("movestogo eats depth", "go movestogo depth 5", "movestogo takes 'depth'"),
    ("softnodes eats depth", "go softnodes depth 5", "softnodes takes 'depth'"),
    # Controls: the same good limit, untouched.
    ("control nodes", "go nodes 50000", "reference"),
    ("control depth", "go depth 5", "reference"),
    # Same shape, but junk BEFORE the good keyword rather than in its value slot.
    ("junk before good keyword", "go xyz nodes 50000", "xyz is not a keyword -> skipped"),
    ("two keywords, bad value first", "go nodes abc depth 5", "abc consumed, depth survives"),
]


def main() -> int:
    exe = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/build/base/forge"
    rows = []
    for form, command, note in CELLS:
        c = run_cell(exe, command, MIDGAME_WHITE, False, 20.0, build=BUILD)
        row = c.as_dict()
        row.update({"verdict": verdict(c), "note": note, "form": form, "keyword": "keyword-eating", "section": "eating"})
        rows.append(row)
        print(
            f'{verdict(c):18s} d={c.max_depth} n={c.last_nodes} bm={c.bestmove} L={c.info_depth_lines} '
            f'stop->{c.stop_bestmove} | {command}',
            flush=True,
        )
    out = Path(__file__).resolve().parent.parent / "evidence"
    with (out / "eating.jsonl").open("w") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
