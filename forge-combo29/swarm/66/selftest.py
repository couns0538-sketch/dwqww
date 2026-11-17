#!/usr/bin/env python3
"""selftest.py - prove the swarm-66 harness can fail before trusting a zero.

Every planted fault below must be CAUGHT. If this script prints PASS on the
planted faults, the harness is blind and no number produced through it counts.

Run:  python3 selftest.py /tmp/w66/build/forge
"""

from __future__ import annotations

import os
import stat
import sys
import tempfile

import ucilib

FAKE_HANG = r"""#!/usr/bin/env python3
import sys, time
for line in sys.stdin:
    line = line.strip()
    if line == "uci":
        print("id name planted-hang", flush=True)
        print("uciok", flush=True)
    elif line == "isready":
        print("readyok", flush=True)
    elif line.startswith("go"):
        pass  # deliberately never answers
"""

FAKE_INVALID = r"""#!/usr/bin/env python3
import sys
for line in sys.stdin:
    line = line.strip()
    if line == "uci":
        print("uciok", flush=True)
    elif line == "isready":
        print("readyok", flush=True)
    elif line.startswith("position"):
        print("info string invalid FEN: planted", flush=True)
    elif line.startswith("go"):
        print("info depth 1 score cp 0 nodes 0 time 0 pv ", flush=True)
        print("bestmove a2a3", flush=True)
"""

FAKE_SLOW = r"""#!/usr/bin/env python3
import sys, time
for line in sys.stdin:
    line = line.strip()
    if line == "uci":
        print("uciok", flush=True)
    elif line == "isready":
        print("readyok", flush=True)
    elif line.startswith("go"):
        time.sleep(0.35)
        print("info depth 1 score cp 0 nodes 1 time 350 pv a2a3", flush=True)
        print("bestmove a2a3", flush=True)
"""

FAKE_DEEP = r"""#!/usr/bin/env python3
import sys
for line in sys.stdin:
    line = line.strip()
    if line == "uci":
        print("uciok", flush=True)
    elif line == "isready":
        print("readyok", flush=True)
    elif line.startswith("position"):
        pass
    elif line.startswith("go"):
        for d in range(1, 6):
            print("info depth %d score cp 1 nodes 10 time 1 pv a2a3" % d, flush=True)
        print("bestmove a2a3", flush=True)
"""

# Prints one info line immediately, then nothing for ever. This is the shape of
# a real engine inside a long iteration: the last output is far earlier than
# the wall time. A harness that measures "time to answer" from the last output
# line reports the info line's time and calls a 0.9 s wait a 0.05 s wait.
FAKE_SILENT_AFTER_INFO = r"""#!/usr/bin/env python3
import sys, time
for line in sys.stdin:
    line = line.strip()
    if line == "uci":
        print("uciok", flush=True)
    elif line == "isready":
        print("readyok", flush=True)
    elif line.startswith("position"):
        pass
    elif line.startswith("go"):
        print("info depth 1 score cp 1 nodes 10 time 1 pv a2a3", flush=True)
        time.sleep(0.9)
"""


def write_fake(script, workdir, name):
    path = os.path.join(workdir, name)
    with open(path, "w") as handle:
        handle.write(script)
    os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return path


def main():
    real = sys.argv[1] if len(sys.argv) > 1 else "/tmp/w66/build/forge"
    check = ucilib.Checker("selftest")
    workdir = tempfile.mkdtemp(prefix="w66_selftest_")

    # 1. A hang must be reported as a timeout, not as a fast answer.
    engine = ucilib.Engine(write_fake(FAKE_HANG, workdir, "fake_hang.py"))
    engine.uci()
    engine.set_position(None)
    result = engine.go("depth 5", timeout=0.6)
    check.add(
        "planted hang -> timed_out",
        result["timed_out"] and result["bestmove"] is None,
        "timed_out=%s bestmove=%r elapsed=%.0fms"
        % (result["timed_out"], result["bestmove"], result["wall_ms"]),
    )
    engine.kill()

    # 2. A planted invalid-FEN line in the POSITION reply must be caught.
    engine = ucilib.Engine(write_fake(FAKE_INVALID, workdir, "fake_invalid.py"))
    engine.uci()
    position = engine.set_position("8/8/8/8/8/8/8/8 w - - 0 1")
    check.add(
        "planted invalid FEN -> position reply",
        position["invalid_fen"],
        "invalid_fen=%s from %d reply lines" % (position["invalid_fen"], len(position["lines"])),
    )
    # ... and the go output of the same engine does NOT show it, which is the
    # exact trap the brief warns about: without the position scan it is lost.
    result = engine.go("depth 2", timeout=5)
    check.add(
        "planted invalid FEN is INVISIBLE in go output",
        not result["invalid_fen"],
        "go-side invalid_fen=%s (proves the position scan is required)" % result["invalid_fen"],
    )
    engine.quit()

    # 3. A slow answer's elapsed time must track the real sleep.
    engine = ucilib.Engine(write_fake(FAKE_SLOW, workdir, "fake_slow.py"))
    engine.uci()
    engine.set_position(None)
    result = engine.go("movetime 350", timeout=5)
    check.add(
        "planted 350 ms delay -> elapsed >= 300",
        result["wall_ms"] >= 300,
        "elapsed=%.0fms" % result["wall_ms"],
    )
    engine.quit()

    # 4. Multi-line info: the parser must take the LAST depth, not the first.
    engine = ucilib.Engine(write_fake(FAKE_DEEP, workdir, "fake_deep.py"))
    engine.uci()
    engine.set_position(None)
    result = engine.go("depth 5", timeout=5)
    reported = result["last_info"]["depth"] if result["last_info"] else None
    check.add(
        "info parser takes the last depth",
        reported == 5 and len(result["info"]) == 5,
        "reported depth=%r over %d info lines" % (reported, len(result["info"])),
    )
    engine.quit()

    # 5. Silence after an info line: the wait must be reported as the WAIT, not
    # as the age of the last output line. This is the bug that made case 1
    # report the last output time for a 330 s wait.
    engine = ucilib.Engine(write_fake(FAKE_SILENT_AFTER_INFO, workdir, "fake_silent.py"))
    engine.uci()
    engine.set_position(None)
    result = engine.go("depth 99", timeout=0.5)
    check.add(
        "silence after one info line -> wall_ms is the WAIT, not the last output",
        result["timed_out"] and result["wall_ms"] >= 400 and result["last_output_ms"] < 200,
        "wall=%.0fms last_output=%.0fms (a last-output measure would report %.0fms)"
        % (result["wall_ms"], result["last_output_ms"], result["last_output_ms"]),
    )
    engine.kill()

    # 6. FEN validation must reject what the engine silently rewrites.
    ok_empty, why_empty = ucilib.check_fen("8/8/8/8/8/8/8/8 w - - 0 1")
    check.add("check_fen rejects an empty board", not ok_empty, why_empty)
    ok_legal, why_legal = ucilib.check_fen(ucilib.chess.STARTING_FEN)
    check.add("check_fen accepts startpos", ok_legal, "accepted")
    ok_move, why_move = ucilib.check_line(ucilib.chess.STARTING_FEN, ["e7e5"])
    check.add("check_line rejects an illegal move", not ok_move, why_move)

    # 7. Control on the real engine: the same harness must produce a real answer.
    engine = ucilib.engine_ready(real)
    position = engine.set_position(None)
    result = engine.go("depth 4", timeout=20)
    check.add(
        "real engine answers depth 4",
        not result["timed_out"] and result["bestmove"] not in (None, ""),
        "bestmove=%r depth=%r elapsed=%.0fms"
        % (result["bestmove"], result["last_info"]["depth"] if result["last_info"] else None, result["wall_ms"]),
    )
    check.add(
        "real engine emits no invalid-FEN line",
        not position["invalid_fen"] and not result["invalid_fen"],
        "position invalid_fen=%s go invalid_fen=%s" % (position["invalid_fen"], result["invalid_fen"]),
    )

    # 8. Planted illegal FEN through the REAL engine must be caught by the scan.
    position = engine.set_position("8/8/8/8/8/8/8/8 w - - 0 1")
    check.add(
        "real engine flags the empty board in the position reply",
        position["invalid_fen"],
        "invalid_fen=%s reply=%r" % (position["invalid_fen"], position["lines"][:2]),
    )
    engine.quit()

    summary = check.summary()
    failed = summary["total"] - summary["passed"]
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
