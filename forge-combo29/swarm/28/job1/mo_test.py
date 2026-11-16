#!/usr/bin/env python3
"""mo_test.py EXE OUT.tsv OVERHEAD — 60 positions at movetime 50 and 500 with MoveOverhead=OVERHEAD.

Shows that the movetime shortfall equals Move Overhead: `hard_limit_ms_ = movetime - overhead`.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from timing import Engine, read_positions  # noqa: E402


def main() -> int:
    exe, out, overhead = sys.argv[1], sys.argv[2], int(sys.argv[3])
    here = os.path.dirname(os.path.abspath(__file__))
    fens = read_positions([os.path.join(here, "O.fens")], 60)
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
    rows = []
    for budget in (50, 500):
        for fen in fens:
            eng.send("ucinewgame")
            eng.send("isready")
            eng.read_until("readyok", 20)
            eng.send(f"position fen {fen}")
            t0 = time.monotonic()
            eng.send(f"go movetime {budget}")
            lines, ok = eng.read_until("bestmove", 60)
            t1 = time.monotonic()
            etime = ""
            for line in lines:
                if line.startswith("info") and " time " in line:
                    parts = line.split()
                    etime = parts[parts.index("time") + 1]
            rows.append((budget, fen, f"{(t1 - t0) * 1000:.3f}", etime, "ok" if ok else "NORESP"))
    eng.close()
    with open(out, "w") as fh:
        fh.write("budget\tfen\twall_ms\tengine_time_ms\tstatus\n")
        for r in rows:
            fh.write("\t".join(str(x) for x in r) + "\n")
    for budget in (50, 500):
        w = sorted(float(r[2]) for r in rows if r[0] == budget)
        print(f"MoveOverhead={overhead} movetime={budget}: n={len(w)} median={w[len(w)//2]:.1f} "
              f"max={w[-1]:.1f} min={w[0]:.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
