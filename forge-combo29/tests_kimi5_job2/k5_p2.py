#!/usr/bin/env python3
"""kimi5 job2 Part 2: clocked searches over UHO positions, one switch per run.
One engine process per run. ucinewgame + isready before every position. Blocking line reads
only (select+TextIOWrapper read-ahead ate a whole search in the smoke test; job-1 style).
Every command is mirrored into an input log (proof the option arrived). Per search: engine's
own last `time`, last finished iteration depth, bestmove (legality-checked), count of
`info string TmFinishIteration hold` and `info string TmNodeShare` lines, wall ms.
Searches here are hard-limited by the engine's own plan (hard <= 2645 ms for these clocks),
so a missing bestmove means a real engine fault: it is recorded as a failure line.

Usage: k5_p2.py <engine> <positions.fens> <label> <setoption-line|NONE> [npositions]
Writes k5_p2_<label>.json and k5_p2_<label>_input.log in the CWD."""
import chess
import json
import subprocess
import sys
import time

ENGINE = sys.argv[1]
FENS = sys.argv[2]
LABEL = sys.argv[3]
SETOPT = sys.argv[4]
NPOS = int(sys.argv[5]) if len(sys.argv) > 5 else 300

# (wtime=btime T ms, winc=binc I ms), in the order the job file gives.
CLOCKS = [(10000, 100), (6000, 100), (3000, 100), (1000, 100), (300, 100),
          (1000, 10), (500, 10), (200, 10)]


def main():
    positions = [l.strip() for l in open(FENS) if l.strip()][:NPOS]
    boards = [chess.Board(f) for f in positions]
    input_log = open(f"k5_p2_{LABEL}_input.log", "w")
    p = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(s):
        input_log.write(s + "\n")
        input_log.flush()
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def readline():
        return p.stdout.readline()

    def wait_prefix(prefix):
        while True:
            line = readline()
            if line == "":
                raise RuntimeError(f"engine closed stdout waiting for {prefix}")
            if line.startswith(prefix):
                return

    send("uci")
    wait_prefix("uciok")
    send("setoption name Threads value 1")
    send("setoption name Hash value 16")
    send("setoption name OwnBook value false")
    if SETOPT != "NONE":
        send(SETOPT)
    send("isready")
    wait_prefix("readyok")

    records = []
    illegal = 0
    failures = 0
    for pi, board in enumerate(boards):
        send("ucinewgame")
        send("isready")
        wait_prefix("readyok")
        send(f"position fen {positions[pi]}")
        for ci, (t, inc) in enumerate(CLOCKS):
            go = f"go wtime {t} btime {t} winc {inc} binc {inc}"
            send(go)
            t0 = time.monotonic_ns()
            best = None
            last_time = None
            last_depth = None
            holds = 0
            adjusts = 0
            while True:
                line = readline()
                if line == "":
                    failures += 1
                    break
                if line.startswith("info depth "):
                    parts = line.split()
                    if "depth" in parts:
                        last_depth = int(parts[parts.index("depth") + 1])
                    if " time " in line:
                        last_time = int(parts[parts.index("time") + 1])
                elif line.startswith("info string TmFinishIteration"):
                    holds += 1
                elif line.startswith("info string TmNodeShare"):
                    adjusts += 1
                elif line.startswith("bestmove"):
                    parts = line.split()
                    best = parts[1] if len(parts) > 1 else "0000"
                    break
            wall_ms = (time.monotonic_ns() - t0) / 1e6
            if best is None:
                records.append({"pos": pi, "clock": ci, "failed": True})
                continue
            try:
                mv = chess.Move.from_uci(best)
                if mv not in board.legal_moves:
                    illegal += 1
            except Exception:
                illegal += 1
            records.append({"pos": pi, "clock": ci, "bestmove": best,
                            "engine_time": last_time, "depth": last_depth,
                            "wall_ms": round(wall_ms, 2), "holds": holds,
                            "adjusts": adjusts})
    send("quit")
    try:
        p.wait(timeout=5)
    except Exception:
        p.kill()
    input_log.close()
    with open(f"k5_p2_{LABEL}.json", "w") as f:
        json.dump({"label": LABEL, "setopt": SETOPT, "clocks": CLOCKS,
                   "n_positions": len(positions), "illegal": illegal,
                   "failures": failures, "records": records}, f)
    print(f"{LABEL}: {len(records)} searches, illegal={illegal}, failures={failures}")


if __name__ == "__main__":
    main()
