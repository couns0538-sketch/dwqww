#!/usr/bin/env python3
"""movetime_sweep.py EXE OUTDIR — the correction experiment for S-F1.

Seat 16's point: the M-10 plan exists, but the ACHIEVED stop time is the end of the last whole
iteration, which undershoots the plan. So the plan alone does not predict the stop.

Grid: movetime in {50, 100, 200, 500} x Move Overhead in {0, 10, 25, 45} = 16 cells.
Per cell: 30 positions (first 30 of O then of G), fresh process, OwnBook false, Threads 1, Hash 16,
`ucinewgame` + `isready` before every `go`.

Per search recorded: wall ms, the engine's own `time` field, the LAST COMPLETED depth (highest depth
seen in an `info depth` line before bestmove), and the plan the code computes
(`hard = max(1, movetime - overhead)`).

Why the last completed depth matters: iterative deepening can only stop at an iteration boundary, so
the achieved time is bounded above by the plan but not reliably NEAR it — it clusters at whatever the
depth that fits costs. This script measures that, per cell.

Usage: movetime_sweep.py EXE OUTDIR
"""
import hashlib
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job1"))
from timing import Engine, read_positions  # noqa: E402

MOVETIMES = (50, 100, 200, 500)
OVERHEADS = (0, 10, 25, 45)
NPOS = 30


def probe_cell(exe, fens, movetime, overhead):
    eng = Engine(exe)
    eng.send("uci")
    eng.read_until("uciok", 20)
    for opt, val in [("OwnBook", "false"), ("Threads", 1), ("Hash", 16),
                     ("Move Overhead", overhead)]:
        eng.send(f"setoption name {opt} value {val}")
        eng.send("isready")
        _l, ok = eng.read_until("readyok", 20)
        if not ok:
            raise SystemExit(f"no readyok for {opt}")
    rows = []
    for fen in fens:
        eng.send("ucinewgame")
        eng.send("isready")
        eng.read_until("readyok", 20)
        eng.send(f"position fen {fen}")
        eng.send("isready")
        eng.read_until("readyok", 20)
        t0 = time.monotonic()
        eng.send(f"go movetime {movetime}")
        out, ok = eng.read_until("bestmove", 60)
        t1 = time.monotonic()
        depth = 0
        etime = ""
        nodes = ""
        for line in out:
            if line.startswith("info depth"):
                f = line.split()
                d = int(f[f.index("depth") + 1])
                if d > depth:
                    depth = d
                if "time" in f:
                    etime = f[f.index("time") + 1]
                if "nodes" in f:
                    nodes = f[f.index("nodes") + 1]
        rows.append({"fen": fen, "wall_ms": (t1 - t0) * 1000.0, "engine_ms": etime,
                     "depth": depth, "nodes": nodes, "ok": ok})
    eng.close()
    return rows


def main() -> int:
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    here = os.path.dirname(os.path.abspath(__file__))
    fens = read_positions([os.path.join(here, "..", "job1", "O.fens"),
                           os.path.join(here, "..", "job1", "G.epd")], NPOS)
    fens = [f.split(";")[0].split(" bm")[0].strip() for f in fens]
    sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    summary = []
    for movetime in MOVETIMES:
        for overhead in OVERHEADS:
            rows = probe_cell(exe, fens, movetime, overhead)
            name = f"mt{movetime}_mo{overhead}"
            with open(os.path.join(outdir, name + ".tsv"), "w") as fh:
                fh.write("fen\twall_ms\tengine_time_ms\tlast_depth\tnodes\tstatus\n")
                for r in rows:
                    fh.write(f"{r['fen']}\t{r['wall_ms']:.3f}\t{r['engine_ms']}\t{r['depth']}\t"
                             f"{r['nodes']}\t{'ok' if r['ok'] else 'NORESP'}\n")
            with open(os.path.join(outdir, name + ".meta"), "w") as fh:
                fh.write(f"exe_started {os.path.abspath(exe)}\n")
                fh.write(f"exe_sha256 {sha}\n")
                fh.write("option OwnBook false\noption Threads 1\noption Hash 16\n")
                fh.write(f"option Move Overhead {overhead}\n")
                fh.write(f"go_line go movetime {movetime}\nplan_hard_ms {max(1, movetime-overhead)}\n")
                fh.write(f"positions {len(rows)}\n")
            depths = {}
            for r in rows:
                depths[r["depth"]] = depths.get(r["depth"], 0) + 1
            summary.append({
                "name": name, "movetime": movetime, "overhead": overhead,
                "plan": max(1, movetime - overhead),
                "median": statistics.median([r["wall_ms"] for r in rows]),
                "max": max(r["wall_ms"] for r in rows),
                "min": min(r["wall_ms"] for r in rows),
                "depths": dict(sorted(depths.items())),
                "ok": sum(1 for r in rows if r["ok"]),
                "n": len(rows),
            })
            print(f"{name}: plan {summary[-1]['plan']} ms, median {summary[-1]['median']:.1f}, "
                  f"depths {summary[-1]['depths']}", flush=True)
    print()
    print("| movetime | MoveOverhead | plan (M-O) ms | n | median wall ms | min | max | last depth "
          "(count) | median/plan |")
    print("|---|---|---|---|---|---|---|---|---|")
    for s in summary:
        ds = " ".join(f"d{d}:{c}" for d, c in s["depths"].items())
        print(f"| {s['movetime']} | {s['overhead']} | {s['plan']} | {s['n']} | {s['median']:.1f} | "
              f"{s['min']:.1f} | {s['max']:.1f} | {ds} | {s['median']/s['plan']:.2f} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
