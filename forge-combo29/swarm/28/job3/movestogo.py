#!/usr/bin/env python3
"""movestogo.py EXE OUTDIR — AREA 8 job 3: movestogo 1, 2, 40 with wtime 1000.

For each movestogo value (1, 2, 40, plus 50 and 51 for the clamp check): 40 positions, one process,
`ucinewgame` + `isready` before every `go`, wall time on a monotonic clock, the engine's own time,
and the fraction of the 1000 ms clock that the search used.

Note: the task says `wtime 1000`; no winc is sent, which is the same as winc 0. The engine's plan
uses `available = 1000 - MoveOverhead(10) = 990`.

Usage: movestogo.py EXE OUTDIR
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job1"))
from timing import Engine, read_positions  # noqa: E402

CLOCK = 1000
VALUES = [1, 2, 40, 50, 51]


def main() -> int:
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    here = os.path.dirname(os.path.abspath(__file__))
    fens = read_positions([os.path.join(here, "..", "job1", "O.fens"),
                           os.path.join(here, "..", "job1", "G.epd")], 40)
    fens = [f.split(";")[0].split(" bm")[0].strip() for f in fens]
    for mtg in VALUES:
        eng = Engine(exe)
        eng.send("uci")
        eng.read_until("uciok", 20)
        for opt, val in [("Threads", 1), ("Hash", 16)]:
            eng.send(f"setoption name {opt} value {val}")
            eng.send("isready")
            eng.read_until("readyok", 20)
        rows = []
        for fen in fens:
            eng.send("ucinewgame")
            eng.send("isready")
            eng.read_until("readyok", 20)
            eng.send(f"position fen {fen}")
            eng.send("isready")
            eng.read_until("readyok", 20)
            t0 = time.monotonic()
            eng.send(f"go wtime {CLOCK} btime {CLOCK} movestogo {mtg}")
            out, ok = eng.read_until("bestmove", 60)
            t1 = time.monotonic()
            best, etime = "", ""
            for line in out:
                if line.startswith("bestmove"):
                    parts = line.split()
                    best = parts[1] if len(parts) > 1 else ""
                if line.startswith("info") and " time " in line:
                    f = line.split()
                    etime = f[f.index("time") + 1]
            rows.append((fen, f"{(t1 - t0) * 1000:.3f}", etime, best, "ok" if ok else "NORESP"))
        eng.close()
        with open(os.path.join(outdir, f"mtg{mtg}.tsv"), "w") as fh:
            fh.write("fen\twall_ms\tengine_time_ms\tbestmove\tstatus\n")
            for r in rows:
                fh.write("\t".join(str(x) for x in r) + "\n")
        with open(os.path.join(outdir, f"mtg{mtg}.meta"), "w") as fh:
            fh.write(f"exe_started {os.path.abspath(exe)}\n")
            fh.write(f"go_line go wtime {CLOCK} btime {CLOCK} movestogo {mtg}\n")
            fh.write("option Threads 1\noption Hash 16\npositions %d\n" % len(rows))
        print(f"mtg{mtg}: {len(rows)} searches")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
