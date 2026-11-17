#!/usr/bin/env python3
"""The 2^63 clock: a HUGE VALID budget, not a dropped limit.

`parse_clock_ms` clamps an over-large magnitude to `kMaxClockMs`
(`uci_clock.hpp`, the `result_out_of_range` branch) instead of rejecting it, so
`wtime 9223372036854775808` sets a clock of ~3.6e16 ms rather than no clock.

On a middlegame both a huge clock and a dropped clock look like "never returns".
On a small board they separate: a huge clock still ends at the depth-64 clamp,
while `go infinite` blocks on `stop`. That is what this measures, so the table
does not have to guess which of the two a CAP cell means.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from go_probe import run_cell  # noqa: E402

BUILD = "base@6b98f217 (g++ 13.3.0, sha256 e06310ec)"
SMALL = "fen 8/8/8/8/8/8/4k3/K1R5 w - - 0 1"
COMMANDS = [
    "go wtime 9223372036854775808",
    "go movetime 9223372036854775808",
    "go wtime abc",
    "go infinite",
]


def main() -> int:
    exe = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/build/base/forge"
    cap = float(sys.argv[2]) if len(sys.argv) > 2 else 90.0
    rows = []
    for command in COMMANDS:
        c = run_cell(exe, command, SMALL, False, cap, build=BUILD)
        rows.append(
            {
                "go": command,
                "position": "K+R v K",
                "returned_on_its_own": c.terminated,
                "elapsed_ms": c.elapsed_ms,
                "max_depth": c.max_depth,
                "bestmove": c.bestmove,
                "bestmove_after_stop": c.stop_bestmove,
                "build": BUILD,
            }
        )
        print(
            f"{command:40s} returned={c.terminated} {c.elapsed_ms:>8.0f}ms d={c.max_depth} "
            f"bm={c.bestmove} stop->{c.stop_bestmove}",
            flush=True,
        )
    out = Path(__file__).resolve().parent.parent / "evidence" / "huge_clock.json"
    out.write_text(json.dumps(rows, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
