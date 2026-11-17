#!/usr/bin/env python3
"""Is "unbounded" unbounded, or bounded at the depth-64 clamp?

Trap 24 in the findings document says `go infinite` is bounded by `stop` or
depth 64, whichever comes first, and that on startpos the 75-second cap was
reached at depth 30 without returning. So "no bestmove in 20 s" does not by
itself establish "never returns".

This runs the unbounded forms with a LONG cap on a SMALL board (K+R v K), where
the tree is small enough that depth 64 is reachable, and reports whether each
one returns on its own. That separates the two claims:
  * "no bestmove within any practical budget on a real position", measured, and
  * "not unbounded in the formal sense; the depth clamp ends it on a small board".
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from go_probe import MIDGAME_WHITE, run_cell, verdict  # noqa: E402

BUILD = "base@6b98f217 (g++ 13.3.0, sha256 e06310ec)"
# Small board: the depth clamp is reachable here, unlike a middlegame.
SMALL = "fen 8/8/8/8/8/8/4k3/K1R5 w - - 0 1"
COMMANDS = ["go nodes abc", "go mate abc", "go nodes", "go infinite"]
CAP = 120.0


def main() -> int:
    exe = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/build/base/forge"
    rows = []
    for position, label in ((SMALL, "K+R v K"), (MIDGAME_WHITE, "middlegame")):
        for command in COMMANDS:
            c = run_cell(exe, command, position, False, CAP, build=BUILD)
            rows.append(
                {
                    "position": label,
                    "go": command,
                    "returned_on_its_own": c.terminated,
                    "elapsed_ms": c.elapsed_ms,
                    "max_depth": c.max_depth,
                    "info_depth_lines": c.info_depth_lines,
                    "bestmove": c.bestmove,
                    "bestmove_after_stop": c.stop_bestmove,
                    "build": BUILD,
                }
            )
            shape = "RETURNED" if c.terminated else f"CAPPED at {CAP:g}s"
            print(f"{label:12s} {command:16s} {shape:18s} d={c.max_depth} bm={c.bestmove} stop->{c.stop_bestmove}", flush=True)
    out = Path(__file__).resolve().parent.parent / "evidence" / "boundedness.json"
    out.write_text(json.dumps(rows, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
