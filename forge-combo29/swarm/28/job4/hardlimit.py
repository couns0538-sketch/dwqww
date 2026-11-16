#!/usr/bin/env python3
"""hardlimit.py EXE OUTDIR — does a clock search ever exceed the engine's own hard limit?

Cells:
  mtg1_w1000    go wtime 1000 btime 1000 movestogo 1     hard 792
  mtg1_w10000   go wtime 10000 btime 10000 movestogo 1   hard 7912
  mt500         go movetime 500                          hard 490
  wt1000        go wtime 1000 btime 1000 winc 10 binc 10 hard 260
  wt500         go wtime 500 btime 500                   hard 294
60 positions per cell. Per search: wall ms, engine's own last-info time, last completed depth, nodes,
bestmove and its legality, and whether it exceeded soft / hard / the GUI clock.

The hard/soft plans are recomputed here from include/forge/clock_plan.hpp with the source defaults and
written into each cell's .meta, so the thresholds in the table can be checked against the code rather
than taken on trust.

Usage: hardlimit.py EXE OUTDIR
"""
import hashlib
import os
import statistics
import sys
import time

import chess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job1"))
from timing import Engine, read_positions  # noqa: E402

OVERHEAD = 10
SOFT_DIV = 22
INC_PCT = 75
HARD_PCT = 60
HARD_MULT = 5
NPOS = 60


def plan_clock(time_ms, inc_ms, mtg=0):
    if time_ms <= OVERHEAD:
        return 0, 0
    avail = time_ms - OVERHEAD
    if mtg > 0:
        m = min(mtg, 50)
        soft = avail // (m + 1) + inc_ms * 3 // 4
        hard = min(avail * 4 // 5, soft * 4)
    else:
        soft = avail // SOFT_DIV + inc_ms * INC_PCT // 100
        hard = min(avail * HARD_PCT // 100, soft * HARD_MULT)
    soft = max(1, min(soft, avail))
    hard = max(1, min(hard, avail))
    if soft > hard:
        soft = hard
    return soft, hard


# The LAST field is `movetime` and must be None for every CLOCK cell. A first version passed a
# number there for the movestogo cells, so the plan was computed as (movetime - overhead) and the
# table showed soft 980 / hard 980 for a cell whose real plan is soft 495 / hard 792. Fixed.
CELLS = [
    ("mtg1_w1000", "go wtime 1000 btime 1000 movestogo 1", 1000, 0, 1, None),
    ("mtg1_w10000", "go wtime 10000 btime 10000 movestogo 1", 10000, 0, 1, None),
    ("mt500", "go movetime 500", None, 0, 0, 500),
    ("wt1000", "go wtime 1000 btime 1000 winc 10 binc 10", 1000, 10, 0, None),
    ("wt500", "go wtime 500 btime 500", 500, 0, 0, None),
]


def cell(exe, fens, name, go, wtime, winc, mtg, movetime, outdir):
    if movetime:
        hard = soft = max(1, movetime - OVERHEAD)
    else:
        soft, hard = plan_clock(wtime, winc, mtg)
    eng = Engine(exe)
    eng.send("uci")
    eng.read_until("uciok", 20)
    for opt, val in [("OwnBook", "false"), ("Threads", 1), ("Hash", 16)]:
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
        eng.send(go)
        out, ok = eng.read_until("bestmove", 120)
        t1 = time.monotonic()
        best, etime, depth, nodes = "", "", 0, 0
        for line in out:
            if line.startswith("bestmove"):
                p = line.split()
                best = p[1] if len(p) > 1 else ""
            if line.startswith("info depth"):
                f = line.split()
                depth = max(depth, int(f[f.index("depth") + 1]))
                if "time" in f:
                    etime = f[f.index("time") + 1]
                if "nodes" in f:
                    nodes = int(f[f.index("nodes") + 1])
        legal = "n/a"
        if best and best != "0000":
            try:
                legal = str(chess.Move.from_uci(best) in chess.Board(fen).legal_moves)
            except ValueError:
                legal = "unparsable"
        rows.append({"fen": fen, "wall": (t1 - t0) * 1000.0, "etime": etime, "depth": depth,
                     "nodes": nodes, "best": best, "legal": legal, "ok": ok})
    eng.close()
    # Written incrementally: a later failure must never discard measurements already taken.
    with open(os.path.join(outdir, name + ".tsv"), "w") as fh:
        fh.write("fen\twall_ms\tengine_time_ms\tlast_depth\tnodes\tbestmove\tlegal\tstatus\n")
        for r in rows:
            fh.write(f"{r['fen']}\t{r['wall']:.3f}\t{r['etime']}\t{r['depth']}\t{r['nodes']}\t"
                     f"{r['best']}\t{r['legal']}\t{'ok' if r['ok'] else 'NORESP'}\n")
            fh.flush()
    with open(os.path.join(outdir, name + ".meta"), "w") as fh:
        fh.write(f"exe_started {os.path.abspath(exe)}\n")
        fh.write(f"exe_sha256 {hashlib.sha256(open(exe, 'rb').read()).hexdigest()}\n")
        fh.write("option OwnBook false\noption Threads 1\noption Hash 16\n")
        fh.write(f"go_line {go}\nplan_soft_ms {soft}\nplan_hard_ms {hard}\n")
        fh.write(f"gui_clock_ms {wtime if wtime is not None else movetime}\n")
        fh.write(f"positions {len(rows)}\n")
    return rows, soft, hard


def main() -> int:
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    here = os.path.dirname(os.path.abspath(__file__))
    # 60 positions from the two sets, interleaved so an unlucky block cannot bias one cell.
    fens = read_positions([os.path.join(here, "..", "job1", "O.fens"),
                           os.path.join(here, "..", "job1", "G.epd")], NPOS * 2)
    fens = [f.split(";")[0].split(" bm")[0].strip() for f in fens]
    fens = fens[:NPOS]
    print("| cell | go line | plan soft | plan hard | n | median wall | max wall | over SOFT | "
          "over HARD | max/hard | max depth on the worst | legal |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for name, go, wtime, winc, mtg, movetime in CELLS:
        rows, soft, hard = cell(exe, fens, name, go, wtime, winc, mtg, movetime, outdir)
        walls = [r["wall"] for r in rows]
        mx = max(walls)
        worst = max(rows, key=lambda r: r["wall"])
        legal = sum(1 for r in rows if r["legal"] == "True")
        print(f"| {name} | `{go}` | {soft} | {hard} | {len(rows)} | {statistics.median(walls):.1f} | "
              f"{mx:.1f} | {sum(1 for w in walls if w > soft)} | {sum(1 for w in walls if w > hard)} | "
              f"{mx/hard:.2f} | d{worst['depth']} ({worst['nodes']} n) | {legal}/{len(rows)} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
