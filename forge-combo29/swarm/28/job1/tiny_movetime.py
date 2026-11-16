#!/usr/bin/env python3
"""tiny_movetime.py EXE — what `go movetime M` does for M at and under the Move Overhead default.

For each (movetime, MoveOverhead) pair: one fresh process, ucinewgame+isready first, wall time to
bestmove on a monotonic clock, and the engine's own reported time. Writes TSV to stdout.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from timing import Engine  # noqa: E402


def main() -> int:
    exe = sys.argv[1]
    fen = sys.argv[2] if len(sys.argv) > 2 else None
    print("movetime\tmove_overhead\twall_ms\tengine_time_ms\tbestmove\tstatus")
    for movetime, overhead in [(50, 10), (11, 10), (10, 10), (5, 10), (1, 10), (0, 10),
                               (50, 40), (10, 40), (5, 40), (50, 0), (1, 0)]:
        eng = Engine(exe)
        eng.send("uci")
        eng.read_until("uciok", 20)
        for name, value in [("Threads", 1), ("Hash", 16), ("Move Overhead", overhead)]:
            eng.send(f"setoption name {name} value {value}")
            eng.send("isready")
            _l, ok = eng.read_until("readyok", 20)
            if not ok:
                print(f"STOP no readyok for {name}", file=sys.stderr)
                return 2
        eng.send("ucinewgame")
        eng.send("isready")
        eng.read_until("readyok", 20)
        eng.send("position startpos" if fen is None else f"position fen {fen}")
        t0 = time.monotonic()
        eng.send(f"go movetime {movetime}")
        lines, ok = eng.read_until("bestmove", 20)
        t1 = time.monotonic()
        best, etime = "", ""
        for line in lines:
            if line.startswith("bestmove"):
                best = line.split()[1] if len(line.split()) > 1 else ""
            if line.startswith("info") and " time " in line:
                parts = line.split()
                etime = parts[parts.index("time") + 1]
        eng.close()
        print(f"{movetime}\t{overhead}\t{(t1-t0)*1000:.2f}\t{etime}\t{best}\t{'ok' if ok else 'NORESP'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
