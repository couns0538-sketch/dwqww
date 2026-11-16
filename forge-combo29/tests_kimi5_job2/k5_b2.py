#!/usr/bin/env python3
"""kimi5 job1 B2: measured overshoot, write(`go`) -> read(`bestmove`), monotonic clock.
One engine process per (position set, go line, threads). ucinewgame + isready before every
position. Every setoption and go line is mirrored into an input log (proof of arrival).
Every bestmove is checked legal with python-chess. The engine's own last reported `time`
is captured beside the wall measurement.

Usage: k5_b2.py <engine> <positions.fens> <label> [wrapper]
Writes k5_b2_<label>.json and k5_b2_<label>_input.log in the CWD."""
import chess
import json
import statistics
import subprocess
import sys
import time

ENGINE = sys.argv[1]
FENS = sys.argv[2]
LABEL = sys.argv[3]
WRAPPER = sys.argv[4] if len(sys.argv) > 4 else None

GO_LINES = [20, 50, 100]
THREADS_SETS = [1, 4]


def run_one(positions, go_line, threads, input_log, wrapper):
    cmd = [wrapper, ENGINE] if wrapper else [ENGINE]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(s):
        input_log.write(s + "\n")
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def readline():
        return p.stdout.readline()

    send("uci")
    while not readline().startswith("uciok"):
        pass
    send(f"setoption name Threads value {threads}")
    send("setoption name Hash value 16")
    send("setoption name OwnBook value false")
    send("isready")
    while not readline().startswith("readyok"):
        pass
    records = []
    illegal = 0
    for fen in positions:
        send("ucinewgame")
        send("isready")
        while not readline().startswith("readyok"):
            pass
        send(f"position fen {fen}")
        send(go_line)
        t0 = time.monotonic_ns()
        best = None
        engine_time = None
        while True:
            line = readline()
            if not line:
                break
            if line.startswith("info depth"):
                parts = line.split()
                if "time" in parts:
                    engine_time = int(parts[parts.index("time") + 1])
            elif line.startswith("bestmove"):
                t1 = time.monotonic_ns()
                parts = line.split()
                best = parts[1] if len(parts) > 1 else None
                break
        if best is None:
            illegal += 1
            continue
        board = chess.Board(fen)
        try:
            if chess.Move.from_uci(best) not in board.legal_moves:
                illegal += 1
        except ValueError:
            illegal += 1
        records.append({"elapsed_ms": (t1 - t0) / 1e6, "engine_time_ms": engine_time,
                        "bestmove": best})
    send("quit")
    p.wait(timeout=20)
    vals = sorted(r["elapsed_ms"] for r in records)
    n = len(vals)
    t = int(go_line.split()[2])
    return {
        "go": go_line, "threads": threads, "n": n, "illegal_or_missing": illegal,
        "median_ms": statistics.median(vals) if n else None,
        "p95_ms": vals[int(0.95 * (n - 1))] if n else None,
        "max_ms": vals[-1] if n else None,
        "over_T": sum(1 for v in vals if v > t),
        "max_engine_time_ms": max((r["engine_time_ms"] or 0) for r in records) if records else None,
        "records": records,
    }


def main():
    positions = [l.strip() for l in open(FENS, encoding="utf-8", errors="replace") if l.strip()]
    out = {"engine": ENGINE, "fens": FENS, "label": LABEL, "runs": []}
    with open(f"k5_b2_{LABEL}_input.log", "w") as input_log:
        for threads in THREADS_SETS:
            for t in GO_LINES:
                go_line = f"go wtime {t} btime {t} winc 0 binc 0"
                res = run_one(positions, go_line, threads, input_log, WRAPPER)
                out["runs"].append(res)
                slim = {k: v for k, v in res.items() if k != "records"}
                print(json.dumps(slim), flush=True)
        # Control 1: harness floor, Threads 1.
        res = run_one(positions, "go depth 1", 1, input_log, WRAPPER)
        res["go"] = "control1: go depth 1"
        out["runs"].append(res)
        print(json.dumps({k: v for k, v in res.items() if k != "records"}), flush=True)
    json.dump(out, open(f"k5_b2_{LABEL}.json", "w"), indent=1)


if __name__ == "__main__":
    main()
